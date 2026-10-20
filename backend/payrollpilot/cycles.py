"""Cycle load + audit services (A-02). Routes stay thin and call these.

No money arithmetic happens here. Audit rules are lane B's ``run_audit``; this
module only stores what it returns, preserves case state across re-audits, and
emits events.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from . import core_bridge, kinds
from .contracts import PayrollCycle, PayrollException
from .db import Database, now_iso
from .events import emit
from .permissions import content_hash
from .settings import Settings

_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,120}$")

# Snapshot list keys -> the entity id lookup used for evidence back-fill.
ENTITY_LISTS = ("workers", "jobs", "time_entries", "receipts", "costs", "obligations")


class LoadError(Exception):
    def __init__(self, status: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail


class CoreContractError(Exception):
    """Core returned output that does not match CONTRACTS. Never a success."""

    def __init__(self, detail: str, errors: list[dict[str, Any]]) -> None:
        super().__init__(detail)
        self.detail = detail
        self.errors = errors


def snapshot_path(settings: Settings, source: str, name: str) -> Path:
    if not _NAME_RE.match(name) or ".." in name:
        raise LoadError(400, "bad_name", "snapshot name must be a plain file stem")
    stem = name[:-5] if name.endswith(".json") else name
    base = settings.fixtures_dir if source == "fixture" else settings.private_snapshots_dir
    return base / f"{stem}.json"


def _strip(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k != "_version"}


def load_cycle(db: Database, settings: Settings, source: str, name: str) -> dict[str, Any]:
    path = snapshot_path(settings, source, name)
    if not path.is_file():
        raise LoadError(404, "snapshot_not_found", f"{source} snapshot {path.name!r} not found")
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LoadError(422, "snapshot_invalid_json", str(exc)) from exc
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("cycle"), dict):
        raise LoadError(422, "snapshot_shape", "snapshot must be an object with a 'cycle' object")

    cycle = dict(snapshot["cycle"])
    if source == "fixture" and cycle.get("provenance") == "real":
        raise LoadError(422, "provenance_mismatch", "a committed fixture cannot claim provenance 'real'")
    # Defaults per CONTRACTS; values present in the snapshot are kept as-is.
    cycle.setdefault("contract_version", "1")
    cycle.setdefault("stage1", {"state": "not_started"})
    cycle.setdefault("stage2", {"state": "not_started"})
    cycle.setdefault("destination", "not_prepared")
    cycle.setdefault("coverage", [])
    try:
        PayrollCycle.model_validate(cycle)
    except ValidationError as exc:
        raise LoadError(422, "cycle_contract", exc.json()) from exc

    cycle_id = cycle["id"]
    snap_hash = content_hash(snapshot)
    existing_snap = db.get_record(kinds.SNAPSHOT, cycle_id)
    existing_cycle = db.get_record(kinds.CYCLE, cycle_id)

    if existing_snap and existing_snap.get("snapshot_hash") == snap_hash and existing_cycle:
        # Same content re-loaded: dedupe (T13), no new versions, no new events.
        return _strip(existing_cycle)

    snap_row = {
        "id": cycle_id,
        "snapshot_id": snapshot.get("snapshot_id"),
        "captured_at": snapshot.get("captured_at"),
        "source": source,
        "name": path.stem,
        "snapshot_hash": snap_hash,
        "provenance": snapshot.get("provenance", cycle.get("provenance")),
        "data": snapshot,
    }
    changed_entries = _changed_time_entries(existing_snap["data"], snapshot) if existing_snap else []
    db.put_record(kinds.SNAPSHOT, snap_row)
    stored = db.put_record(kinds.CYCLE, cycle)
    if changed_entries:
        from .corrections import invalidate_for_source_change

        invalidate_for_source_change(db, cycle_id, changed_entries)
    counts = {k: len(snapshot.get(k) or []) for k in ENTITY_LISTS}
    if not existing_cycle:
        emit(db, type="cycle.created", actor="system", cycle_id=cycle_id,
             summary=f"Cycle {cycle_id} {cycle['period_start']}..{cycle['period_end']} loaded from {source}",
             refs={"source": source, "name": path.stem, "provenance": cycle.get("provenance")})
    emit(db, type="snapshot.captured", actor="system", cycle_id=cycle_id,
         summary=f"Snapshot {snapshot.get('snapshot_id')} stored ({counts['time_entries']} time entries)",
         refs={"snapshot_id": snapshot.get("snapshot_id"), "snapshot_hash": snap_hash, "counts": counts,
               "replaced_previous": bool(existing_snap)})
    return _strip(stored)


def _changed_time_entries(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """Time entry ids whose version_hash changed or that disappeared."""
    before = {te["id"]: te.get("version_hash") for te in old.get("time_entries") or []}
    after = {te["id"]: te.get("version_hash") for te in new.get("time_entries") or []}
    return sorted(i for i, v in before.items() if after.get(i, "<removed>") != v)


def corrected_snapshot(db: Database, cycle_id: str) -> dict[str, Any] | None:
    """Source snapshot with APPLIED local corrections overlaid. The source
    snapshot itself is never modified (source systems are read-only)."""
    snapshot = get_snapshot(db, cycle_id)
    if snapshot is None:
        return None
    applied = [c for c in db.list_records(kinds.CORRECTION, cycle_id=cycle_id) if c.get("state") == "applied"]
    if not applied:
        return snapshot
    view = json.loads(json.dumps(snapshot))
    index = _entity_index(view)
    for corr in sorted(applied, key=lambda c: c.get("applied_at") or ""):
        after = corr.get("after") or {}
        target_id = next((after[k] for k in ("time_entry_id", "cost_id", "worker_id", "job_id") if after.get(k) and after[k] in index), None)
        if target_id is None:
            continue
        rec = index[target_id]
        for key, value in after.items():
            if key.endswith("_id") and value == target_id:
                continue
            rec[key] = value
        rec.setdefault("local_corrections", []).append(corr["id"])
    return view


def get_cycle(db: Database, cycle_id: str) -> dict[str, Any] | None:
    rec = db.get_record(kinds.CYCLE, cycle_id)
    return _strip(rec) if rec else None


def get_snapshot(db: Database, cycle_id: str) -> dict[str, Any] | None:
    row = db.get_record(kinds.SNAPSHOT, cycle_id)
    return row["data"] if row else None


def _entity_index(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for key in ENTITY_LISTS:
        for rec in snapshot.get(key) or []:
            if isinstance(rec, dict) and "id" in rec:
                idx[rec["id"]] = rec
    return idx


def _backfill_evidence(exc: dict[str, Any], index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Evidence = the source refs of the records the exception points at. Only
    used when core returned none; never invents a ref."""
    refs = exc.get("entity_refs") or {}
    ids: list[str] = []
    for key in ("time_entry_ids", "job_ids", "cost_ids"):
        ids.extend(refs.get(key) or [])
    if refs.get("worker_id"):
        ids.append(refs["worker_id"])
    out = []
    for rid in ids:
        rec = index.get(rid) or {}
        ref = rec.get("source_ref") or rec.get("jobber_ref") or rec.get("gusto_ref")
        if ref:
            out.append(ref)
    return out


def _provenance_for(exc: dict[str, Any], snapshot: dict[str, Any], index: dict[str, dict[str, Any]]) -> str:
    if exc.get("provenance"):
        return exc["provenance"]
    refs = exc.get("entity_refs") or {}
    for rid in (refs.get("time_entry_ids") or []) + (refs.get("cost_ids") or []) + (refs.get("job_ids") or []):
        if (index.get(rid) or {}).get("provenance") == "seeded_issue":
            return "seeded_issue"
    return "real" if snapshot.get("provenance") == "real" else "synthetic"


# Fields core owns (detection content). Case-state fields stay with the coordinator.
_DETECTION_FIELDS = (
    "category", "title", "observed", "expected", "evidence", "entity_refs", "stage_impact",
    "dollars_affected_cents", "intended_respondent_role", "provenance",
)


def run_cycle_audit(db: Database, cycle_id: str) -> dict[str, Any]:
    snapshot = corrected_snapshot(db, cycle_id)
    if snapshot is None:
        raise KeyError(cycle_id)
    started = now_iso()
    raw = core_bridge.run_audit(snapshot)
    index = _entity_index(snapshot)

    prepared: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for i, exc in enumerate(raw):
        exc = dict(exc)
        exc["cycle_id"] = cycle_id
        exc.setdefault("state", "detected")
        exc.setdefault("owner_agent", "audit")
        exc.setdefault("message_ids", [])
        exc.setdefault("resolution_id", None)
        exc.setdefault("dollars_affected_cents", None)
        if not exc.get("evidence"):
            exc["evidence"] = _backfill_evidence(exc, index)
        exc["provenance"] = _provenance_for(exc, snapshot, index)
        try:
            PayrollException.model_validate(exc)
        except ValidationError as ve:
            errors.append({"index": i, "id": exc.get("id"), "errors": json.loads(ve.json())})
            continue
        prepared.append(exc)
    if errors:
        emit(db, type="audit.completed", actor="audit", cycle_id=cycle_id,
             summary=f"Audit FAILED contract validation for {len(errors)} of {len(raw)} exceptions; nothing stored",
             refs={"ok": False, "audit_mode": core_bridge.AUDIT_MODE, "errors": len(errors)})
        raise CoreContractError("core run_audit output failed CONTRACTS validation", errors)

    now = now_iso()
    new_ids: list[str] = []
    for exc in prepared:
        existing = db.get_record(kinds.EXCEPTION, exc["id"])
        if existing is None:
            exc["created_at"] = exc.get("created_at") or now
            exc["updated_at"] = now
            db.put_record(kinds.EXCEPTION, exc)
            new_ids.append(exc["id"])
            emit(db, type="exception.detected", actor="audit", cycle_id=cycle_id,
                 summary=f"{exc['category']}: {exc['title']}",
                 refs={"exception_id": exc["id"], "category": exc["category"], "entity_refs": exc.get("entity_refs"),
                       "provenance": exc["provenance"]})
            continue
        # Re-audit: keep case state (state, owner_agent, messages, resolution); refresh detection fields if changed.
        merged = _strip(existing)
        changed = False
        for f in _DETECTION_FIELDS:
            if f in exc and merged.get(f) != exc[f]:
                merged[f] = exc[f]
                changed = True
        # CONTRACTS: resolved -> detected (reopen) on SOURCE CHANGE: a resolved case whose
        # detection content changed. A case resolved by reply but still detected unchanged
        # (e.g. a long shift confirmed legitimate) stays resolved.
        reopened = merged.get("state") == "resolved" and changed
        if reopened:
            merged["state"] = "detected"
            merged.pop("resolved_by_correction_id", None)
            changed = True
        if changed:
            merged["updated_at"] = now
            db.put_record(kinds.EXCEPTION, merged)
        if reopened:
            emit(db, type="exception.state_changed", actor="audit", cycle_id=cycle_id,
                 summary=f"{exc['id']}: resolved -> detected (detected again)",
                 refs={"exception_id": exc["id"], "from": "resolved", "to": "detected"})

    current_ids = {e["id"] for e in prepared}
    all_for_cycle = list_exceptions(db, cycle_id)
    not_redetected = [e["id"] for e in all_for_cycle if e["id"] not in current_ids]
    emit(db, type="audit.completed", actor="audit", cycle_id=cycle_id,
         summary=f"Audit found {len(prepared)} exceptions ({len(new_ids)} new) [{core_bridge.AUDIT_MODE}]",
         refs={"ok": True, "audit_mode": core_bridge.AUDIT_MODE, "count": len(prepared), "new_ids": new_ids,
               "not_redetected_ids": not_redetected, "started_at": started})
    return {"exceptions": [e for e in all_for_cycle if e["id"] in current_ids], "audit_mode": core_bridge.AUDIT_MODE}


def list_exceptions(
    db: Database, cycle_id: str, *, stage: str | None = None, category: str | None = None, state: str | None = None
) -> list[dict[str, Any]]:
    out = [_strip(e) for e in db.list_records(kinds.EXCEPTION, cycle_id=cycle_id, category=category, state=state)]
    if stage in {"stage1", "1", "stage1_wages"}:
        out = [e for e in out if (e.get("stage_impact") or {}).get("stage1_wages", "none") != "none"]
    elif stage in {"stage2", "2", "stage2_costs"}:
        out = [e for e in out if (e.get("stage_impact") or {}).get("stage2_costs", "none") != "none"]
    return out


def exception_detail(db: Database, exception_id: str) -> dict[str, Any] | None:
    exc = db.get_record(kinds.EXCEPTION, exception_id)
    if exc is None:
        return None
    exc = _strip(exc)
    batches = [_strip(b) for b in db.list_records(kinds.MESSAGE_BATCH) if exception_id in (b.get("exception_ids") or [])]
    batch_ids = {b["id"] for b in batches}
    inbound = [_strip(m) for m in db.list_records(kinds.INBOUND) if m.get("correlated_batch_id") in batch_ids]
    resolution = None
    if exc.get("resolution_id"):
        r = db.get_record(kinds.RESOLUTION, exc["resolution_id"])
        resolution = _strip(r) if r else None
    if resolution is None:
        rs = db.list_records(kinds.RESOLUTION, exception_id=exception_id)
        resolution = _strip(rs[-1]) if rs else None
    correction = None
    if resolution:
        cs = db.list_records(kinds.CORRECTION, resolution_id=resolution["id"])
        correction = _strip(cs[-1]) if cs else None
    return {**exc, "messages": {"outbound": batches, "inbound": inbound}, "resolution": resolution, "correction": correction}
