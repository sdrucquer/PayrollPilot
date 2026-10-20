"""Local corrections (A-04). Never a source write: an applied correction is an
overlay on the stored snapshot (see ``cycles.corrected_snapshot``).

Calculation impact comes from lane B's ``propose_correction``; without it the
propose route returns 501 rather than an unknown impact presented as known.
"""

from __future__ import annotations

from typing import Any

from . import core_bridge, cycles, kinds
from .approvals import invalidate_for_target, source_versions_for_correction
from .db import Database, now_iso
from .events import emit, new_id
from .permissions import check_apply, correction_version

_TARGET_KEYS = ("time_entry_id", "cost_id", "worker_id", "job_id")


class CorrectionError(Exception):
    def __init__(self, status: int, code: str, detail: str, extra: dict[str, Any] | None = None) -> None:
        super().__init__(detail)
        self.status, self.code, self.detail, self.extra = status, code, detail, extra or {}


def _strip(r: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in r.items() if k != "_version"}


def _target(view: dict[str, Any], after: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    index = cycles._entity_index(view)
    for key in _TARGET_KEYS:
        rid = after.get(key)
        if rid:
            if rid not in index:
                raise CorrectionError(404, "target_not_found", f"{key} {rid} not in cycle snapshot")
            return key, index[rid]
    raise CorrectionError(422, "no_target", f"after must name one of {_TARGET_KEYS}")


# lane B CorrectionError.code -> HTTP status. Conflicts with current data are
# 409 (re-read and re-propose); requests core cannot express are 422.
_CORE_ERROR_STATUS = {
    "stale_before": 409,
    "allocation_mismatch": 409,
    "target_not_found": 404,
    "unknown_kind": 422,
}


def propose(db: Database, *, resolution_id: str | None, kind: str, after: dict[str, Any], cycle_id: str | None = None) -> dict[str, Any]:
    resolution = db.get_record(kinds.RESOLUTION, resolution_id) if resolution_id else None
    if resolution_id and resolution is None:
        raise CorrectionError(404, "resolution_not_found", f"resolution {resolution_id} not found")
    cycle_id = (resolution or {}).get("cycle_id") or cycle_id
    if not cycle_id:
        raise CorrectionError(422, "cycle_unknown", "resolution_id (or cycle_id) is required")
    view = cycles.corrected_snapshot(db, cycle_id)
    if view is None:
        raise CorrectionError(404, "cycle_not_found", f"cycle {cycle_id} not found")
    key, rec = _target(view, after)
    before = {k: (rec.get(k) if not (k == key) else rec["id"]) for k in after}
    if core_bridge.propose_correction is None:
        raise CorrectionError(501, "core_not_merged", "calculation impact needs payrollpilot_core.corrections.propose_correction")
    try:
        core_out = dict(core_bridge.propose_correction(kind, before, after, view, resolution_id=resolution_id) or {})
    except Exception as exc:  # lane B CorrectionError(code, message)
        code = getattr(exc, "code", None)
        if code is None:
            raise
        raise CorrectionError(_CORE_ERROR_STATUS.get(code, 422), code, str(exc)) from exc
    correction = {
        "id": core_out.get("id") or new_id("corr"),
        "resolution_id": resolution_id,
        "kind": kind,
        "before": before,
        "after": after,
        "calculation_impact": core_out.get("calculation_impact"),
        "blockers": core_out.get("blockers") or [],
        "approval_id": None,
        "state": "proposed",
        "applied_at": None,
        "cycle_id": cycle_id,  # extension, see PR note; lets approvals bind to source versions
    }
    db.put_record(kinds.CORRECTION, correction)
    correction = with_target_version(db, correction)
    emit(db, type="correction.proposed", actor="resolution", cycle_id=cycle_id,
         summary=f"Correction {correction['id']} proposed ({kind})",
         refs={"correction_id": correction["id"], "resolution_id": resolution_id,
               "target_version": correction["target_version"], "calculation_impact": correction["calculation_impact"]})
    return correction


def with_target_version(db: Database, corr: dict[str, Any]) -> dict[str, Any]:
    """Adds the version the owner must approve (computed at read time, since it
    includes the current source version hashes)."""
    corr = _strip(corr)
    corr["target_version"] = correction_version(corr, source_versions_for_correction(db, corr))
    return corr


def readiness_view(db: Database, cycle_id: str, policies: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Readiness via core on the corrected view; None means 'not computed', never 'ready'."""
    if core_bridge.cycle_readiness is None:
        return None
    view = cycles.corrected_snapshot(db, cycle_id) or {}
    return core_bridge.cycle_readiness(view, cycles.list_exceptions(db, cycle_id), policies)


def _readiness_snapshot(db: Database, cycle_id: str, policies: dict[str, Any] | None = None) -> dict[str, Any] | None:
    r = readiness_view(db, cycle_id, policies)
    if r is None:
        return None
    return {"stage1": r["stage1"], **{i["id"]: i.get("readiness") for i in r.get("items") or []}}


def apply(db: Database, correction_id: str, policies: dict[str, Any] | None = None) -> dict[str, Any]:
    corr = db.get_record(kinds.CORRECTION, correction_id)
    if corr is None:
        raise CorrectionError(404, "correction_not_found", f"correction {correction_id} not found")
    corr = _strip(corr)
    if corr.get("state") == "applied":
        raise CorrectionError(409, "already_applied", "correction already applied")
    approvals = db.approvals_for_target(correction_id, state="active")
    approval = approvals[-1] if approvals else None
    sv = source_versions_for_correction(db, corr)
    check_apply(corr, approval, sv)  # raises PermissionDenied -> 403
    cycle_id = corr["cycle_id"]
    before_ready = _readiness_snapshot(db, cycle_id, policies)

    applied = dict(corr, state="applied", applied_at=now_iso(), approval_id=approval["id"])
    db.put_record(kinds.CORRECTION, applied)
    emit(db, type="correction.applied", actor="owner", cycle_id=cycle_id,
         summary=f"Correction {correction_id} applied locally (no source write)",
         refs={"correction_id": correction_id, "approval_id": approval["id"], "source_versions": sv,
               "calculation_impact": corr.get("calculation_impact")})

    audit = cycles.run_cycle_audit(db, cycle_id)
    after_ready = _readiness_snapshot(db, cycle_id, policies)
    emit(db, type="recalc.completed", actor="payroll", cycle_id=cycle_id,
         summary="Re-audited corrected view" + ("" if after_ready is not None else "; readiness not computed (core not merged)"),
         refs={"correction_id": correction_id, "exception_count": len(audit["exceptions"]),
               "readiness": "core" if after_ready is not None else "missing"})
    readiness_changes = None
    if after_ready is not None:
        before_ready = before_ready or {}
        readiness_changes = [
            {"scope": k, "before": before_ready.get(k), "after": v}
            for k, v in after_ready.items() if before_ready.get(k) != v
        ]
        # Only affected items get an event (PRD: update only the relevant readiness).
        for ch in readiness_changes:
            emit(db, type="readiness.changed", actor="payroll", cycle_id=cycle_id,
                 summary=f"Readiness changed for {ch['scope']} after correction {correction_id}",
                 refs={"correction_id": correction_id, "scope": ch["scope"],
                       "before_state": (ch["before"] or {}).get("state"), "after_state": (ch["after"] or {}).get("state")})
    return {"correction": applied, "readiness_changes": readiness_changes, "exceptions": audit["exceptions"]}


def invalidate_for_source_change(db: Database, cycle_id: str, changed_entry_ids: list[str]) -> list[str]:
    """T16: a source record changed after approval -> approvals on corrections
    touching it are invalidated and the correction is marked invalidated."""
    changed = set(changed_entry_ids)
    hit: list[str] = []
    for corr in db.list_records(kinds.CORRECTION, cycle_id=cycle_id):
        if corr.get("state") not in {"proposed", "approved"}:
            continue
        touched = {side.get("time_entry_id") for side in (corr.get("before") or {}, corr.get("after") or {})}
        if not touched & changed:
            continue
        invalidate_for_target(db, corr["id"], "source record changed after approval", cycle_id=cycle_id)
        db.put_record(kinds.CORRECTION, dict(_strip(corr), state="invalidated"))
        hit.append(corr["id"])
    return hit
