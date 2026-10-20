"""Local corrections: proposals with before/after and calculation impact. Pure; never a source write.

`propose_correction(kind, before, after, snapshot)` validates that `before` matches the current snapshot
(stale proposals are refused), builds a corrected view, and computes impact by re-running the calculation
on that view:
- job_allocation (T02): wages delta comes from the changed entries only (0 for a pure reallocation);
  job labor deltas per job. An already-paid entry never creates a new wage payment.
- time_confirmation (T20): reconciles the whole affected workweek against prior recognized payroll for
  that week; if prior payroll for the week is unknown -> blocker prior_recognition_unknown (no
  new-hours x rate supplement).
- rate_confirmation: before/after gross per worker; changes to already-paid entries need an adjustment
  decision.
- cost_link: job cost deltas from the new allocation (allocations must reconcile to the cost total).
- identity_merge: unsupported in this pilot (explicit error).

`apply_corrections(snapshot, corrections)` overlays applied corrections, mirroring the backend's
corrected-snapshot overlay: the record named by an `<entity>_id` key in `after` receives the other keys.
"""
from __future__ import annotations

import copy
from decimal import Decimal

from .audit import verified_rate_cents
from .ids import content_hash
from .money import gross_wages, gross_wages_exact, to_cents
from .time import workweek_for

KINDS = ("job_allocation", "rate_confirmation", "cost_link", "identity_merge", "time_confirmation")
_TARGET_KEYS = ("time_entry_id", "cost_id", "worker_id", "job_id")
_COLLECTIONS = {"time_entry_id": "time_entries", "cost_id": "costs", "worker_id": "workers", "job_id": "jobs"}


class CorrectionError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def _target(snapshot: dict, after: dict) -> tuple[str, dict]:
    for key in _TARGET_KEYS:
        rid = after.get(key)
        if not rid:
            continue
        for rec in snapshot.get(_COLLECTIONS[key], []):
            if rec["id"] == rid:
                return key, rec
    raise CorrectionError("target_not_found", f"no record for any of {_TARGET_KEYS} in {after}")


def apply_corrections(snapshot: dict, corrections: list[dict]) -> dict:
    """Corrected view (deep copy) with every correction in `corrections` overlaid in order."""
    view = copy.deepcopy(snapshot)
    for corr in corrections:
        after = corr.get("after") or {}
        key, rec = _target(view, after)
        for k, v in after.items():
            if k == key:
                continue
            rec[k] = copy.deepcopy(v)
        rec.setdefault("local_corrections", []).append(corr.get("id"))
    return view


def _entry_wage(snapshot: dict, entry: dict) -> int | None:
    w = next((x for x in snapshot.get("workers", []) if x["id"] == entry["worker_id"]), None)
    return gross_wages(entry.get("duration_minutes"), verified_rate_cents(w, entry["date"]))


def _entries_by_id(snapshot: dict) -> dict[str, dict]:
    return {e["id"]: e for e in snapshot.get("time_entries", [])}


def _labor_deltas(before_snap: dict, after_snap: dict, entry_ids: list[str]) -> tuple[list[dict], int | None, list[dict]]:
    """Per-job labor deltas and the wage delta, computed over the changed entries only."""
    b_entries, a_entries = _entries_by_id(before_snap), _entries_by_id(after_snap)
    job_delta: dict[str, int | None] = {}
    wage_delta: int | None = 0
    blockers = []
    for tid in entry_ids:
        b, a = b_entries[tid], a_entries[tid]
        wb, wa = _entry_wage(before_snap, b), _entry_wage(after_snap, a)
        if wb is None or wa is None:
            wage_delta = None
        elif wage_delta is not None:
            wage_delta += wa - wb
            if wa != wb and b.get("paid_status") == "paid_prior_cycle":
                blockers.append({"code": "paid_adjustment_decision",
                                 "label": f"{tid} was paid in a prior run: an adjustment needs an owner decision",
                                 "exception_id": None})
        for job, sign, wage in ((b.get("job_id"), -1, wb), (a.get("job_id"), 1, wa)):
            if job is None:
                continue
            cur = job_delta.get(job, 0)
            job_delta[job] = None if (cur is None or wage is None) else cur + sign * wage
    deltas = [{"job_id": j, "labor_delta_cents": d} for j, d in sorted(job_delta.items()) if d != 0]
    return deltas, wage_delta, blockers


def _prior_recognized_cents(snapshot: dict, worker_id: str, week: dict) -> int | None:
    """Gross wages already recognized for this worker and workweek (from wage obligations). None if unknown."""
    for o in snapshot.get("obligations", []):
        ep = o.get("earning_period") or {}
        if (o.get("kind") == "wages" and o.get("worker_id") == worker_id
                and ep.get("start") == week["start"] and ep.get("end") == week["end"]):
            return o.get("gross_cents")
    return None


def _week_gross(snapshot: dict, worker_id: str, week_start: str) -> tuple[int | None, int | None]:
    weeks = snapshot["cycle"]["workweeks"]
    w = next((x for x in snapshot.get("workers", []) if x["id"] == worker_id), None)
    minutes, total = 0, Decimal(0)
    for e in snapshot.get("time_entries", []):
        if e["worker_id"] != worker_id or workweek_for(e["date"], weeks) != week_start:
            continue
        part = gross_wages_exact(e.get("duration_minutes"), verified_rate_cents(w, e["date"]))
        if part is None or e.get("duration_minutes") is None:
            return None, None
        minutes += e["duration_minutes"]
        total += part
    return minutes, to_cents(total)


def propose_correction(kind: str, before: dict, after: dict, snapshot: dict, resolution_id: str | None = None) -> dict:
    """Return a CONTRACTS LocalCorrection (state proposed) with calculation_impact and blockers."""
    if kind not in KINDS:
        raise CorrectionError("unknown_kind", kind)
    if kind == "identity_merge":
        raise CorrectionError("unsupported:identity_merge", "identity merges are not supported in this pilot")
    key, rec = _target(snapshot, after)
    if before.get(key) not in (None, rec["id"]):
        raise CorrectionError("target_mismatch", "before and after name different records")
    stale = {k: v for k, v in before.items() if k != key and rec.get(k) != v}
    if stale:
        raise CorrectionError("stale_before", f"before does not match current snapshot for {sorted(stale)}")

    view = apply_corrections(snapshot, [{"id": "corr_preview", "after": after}])
    impact: dict = {"stage1_wages_delta_cents": 0, "job_costing_delta": []}
    blockers: list[dict] = []

    if kind == "job_allocation":
        if key != "time_entry_id" or "job_id" not in after:
            raise CorrectionError("bad_payload", "job_allocation needs after.time_entry_id and after.job_id")
        if after["job_id"] is not None and after["job_id"] not in {j["id"] for j in snapshot.get("jobs", [])}:
            raise CorrectionError("unknown_job", after["job_id"])
        deltas, wage_delta, blockers = _labor_deltas(snapshot, view, [rec["id"]])
        impact = {"stage1_wages_delta_cents": wage_delta, "job_costing_delta": deltas}

    elif kind == "time_confirmation":
        if key != "time_entry_id":
            raise CorrectionError("bad_payload", "time_confirmation needs after.time_entry_id")
        new = _entries_by_id(view)[rec["id"]]
        weeks = snapshot["cycle"]["workweeks"]
        wk_start = workweek_for(new["date"], weeks)
        deltas, _, _ = _labor_deltas(snapshot, view, [rec["id"]])
        recon = {"worker_id": new["worker_id"], "workweek_start": wk_start, "minutes_after": None,
                 "gross_after_cents": None, "prior_recognized_cents": None, "reconciled_delta_cents": None}
        wage_delta = None
        if wk_start is None:
            blockers.append({"code": "outside_cycle", "label": "Entry is outside this cycle's workweeks",
                             "exception_id": None})
        else:
            week = next(w for w in weeks if w["start"] == wk_start)
            minutes, gross_after = _week_gross(view, new["worker_id"], wk_start)
            prior = _prior_recognized_cents(snapshot, new["worker_id"], week)
            recon.update(minutes_after=minutes, gross_after_cents=gross_after, prior_recognized_cents=prior)
            if gross_after is None:
                blockers.append({"code": "amount_unknown:wages", "label": "Week gross unknown (minutes or rate)",
                                 "exception_id": None})
            if prior is None:
                blockers.append({"code": "prior_recognition_unknown",
                                 "label": f"Prior payroll for week {wk_start} unknown: reconcile the whole week first (T20)",
                                 "exception_id": None})
            if gross_after is not None and prior is not None:
                wage_delta = gross_after - prior
                recon["reconciled_delta_cents"] = wage_delta
            if minutes is not None and minutes > 2400:
                blockers.append({"code": "policy_missing:O02_overtime",
                                 "label": "Week exceeds 40h: overtime treatment comes from provider/approved policy (O02)",
                                 "exception_id": None})
        impact = {"stage1_wages_delta_cents": wage_delta, "job_costing_delta": deltas, "workweek_reconciliation": recon}

    elif kind == "rate_confirmation":
        if key != "worker_id":
            raise CorrectionError("bad_payload", "rate_confirmation needs after.worker_id")
        ids = [e["id"] for e in snapshot.get("time_entries", []) if e["worker_id"] == rec["id"]]
        deltas, wage_delta, blockers = _labor_deltas(snapshot, view, ids)
        from .readiness import worker_gross_cents  # local import: readiness imports audit, not us
        impact = {"stage1_wages_delta_cents": wage_delta, "job_costing_delta": deltas,
                  "worker_gross": {"worker_id": rec["id"], "before_cents": worker_gross_cents(snapshot, rec["id"]),
                                   "after_cents": worker_gross_cents(view, rec["id"])}}
        if impact["stage1_wages_delta_cents"] is None and impact["worker_gross"]["after_cents"] is not None:
            blockers.append({"code": "first_computation", "label": "Gross was unknown before; review the new amount",
                             "exception_id": None})

    elif kind == "cost_link":
        if key != "cost_id" or "job_allocations" not in after:
            raise CorrectionError("bad_payload", "cost_link needs after.cost_id and after.job_allocations")
        total = rec.get("amount_cents") if "amount_cents" not in after else after["amount_cents"]
        alloc_sum = sum(a["amount_cents"] for a in after["job_allocations"])
        if total is None:
            raise CorrectionError("amount_unknown", "cost amount unknown; resolve the conflict first")
        if alloc_sum != total:
            raise CorrectionError("allocation_mismatch", f"allocations {alloc_sum} != cost {total}")
        old = {a["job_id"]: a["amount_cents"] for a in rec.get("job_allocations", [])}
        new = {a["job_id"]: a["amount_cents"] for a in after["job_allocations"]}
        impact["job_costing_delta"] = [{"job_id": j, "cost_delta_cents": new.get(j, 0) - old.get(j, 0)}
                                       for j in sorted(set(old) | set(new)) if new.get(j, 0) != old.get(j, 0)]

    body = {"kind": kind, "before": before, "after": after, "calculation_impact": impact}
    return {"id": "corr_" + content_hash(body)[7:17], "resolution_id": resolution_id, "kind": kind,
            "before": before, "after": after, "calculation_impact": impact, "blockers": blockers,
            "approval_id": None, "state": "proposed", "applied_at": None,
            "target_version": content_hash(body)}
