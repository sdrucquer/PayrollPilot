"""Scoped readiness (PRD 11.3). Every UI card renders one Readiness dict.

Rules encoded here:
- Stage 1 is partial-by-worker: a worker is ready only when no wage-blocking exception touches them.
- Each Stage 2 item has its own blockers. A manager-pool blocker never appears on a commission card;
  commission, tip, cost or pool blockers never invalidate wages (T09, T24).
- Unknown money is None and sets unknown_amount; it is never 0.
- State vocabulary: worker/stage1 -> ready|partial|blocked; quote/marketing/tip -> ready|pending|not_meaningful;
  manager pool -> ready|blocked (final distributions are blocked while anything relevant is open).

Blocker codes: exception:<exc_id>, policy_missing:<O-id or key>, coverage:<dataset>, and readiness-only codes
stage1_exposure, prior_payment_unknown, allocation_provisional:<rcpt_id>, commissions_pending,
amount_unknown:wages, component_unknown:<key>.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from . import CALC_VERSION
from .audit import verified_rate_cents
from .calc import CalcBlocked, quote_pool
from .money import gross_wages_exact, sum_known, to_cents
from .time import in_period, weekly_minutes

OPEN = lambda e: e.get("state") != "resolved"  # noqa: E731


def _readiness(state, scope, blockers, unknown_amount, now=None) -> dict:
    return {"state": state, "scope": scope, "blockers": blockers, "unknown_amount": bool(unknown_amount),
            "calculation_version": CALC_VERSION, "last_computed_at": now}


def _exc_blocker(e: dict) -> dict:
    return {"code": f"exception:{e['id']}", "label": e["title"], "exception_id": e["id"]}


def _cov_blocker(e: dict) -> list[dict]:
    return [{"code": f"coverage:{key.split(':', 1)[1]}", "label": e["title"], "exception_id": e["id"]}
            for key in e["entity_refs"].get("coverage", [])]


def _dedupe(blockers: list[dict]) -> list[dict]:
    seen, out = set(), []
    for b in blockers:
        if b["code"] not in seen:
            seen.add(b["code"])
            out.append(b)
    return out


def _policies(snapshot: dict, policies: dict | None) -> dict:
    merged = dict(snapshot.get("policies") or {})
    merged.update(policies or {})
    return merged


def cycle_entries(snapshot: dict) -> list[dict]:
    c = snapshot["cycle"]
    return [e for e in snapshot.get("time_entries", []) if in_period(e["date"], c["period_start"], c["period_end"])]


# ------------------------------------------------------------------ Stage 1
def worker_gross_cents(snapshot: dict, worker_id: str) -> int | None:
    """New-cycle gross for one worker: per workweek, per work-date-effective verified rate, summed exactly,
    rounded once. None when any minutes or rate are unknown or identity is unverified."""
    workers = {w["id"]: w for w in snapshot.get("workers", [])}
    w = workers.get(worker_id)
    entries = [e for e in cycle_entries(snapshot) if e["worker_id"] == worker_id]
    if w is None:
        return None
    total = Decimal(0)
    for e in entries:
        part = gross_wages_exact(e.get("duration_minutes"), verified_rate_cents(w, e["date"]))
        if part is None:
            return None
        total += part
    return to_cents(total)


def worker_readiness(snapshot: dict, worker_id: str, exceptions: list[dict], now=None) -> dict:
    w = next((x for x in snapshot.get("workers", []) if x["id"] == worker_id), None)
    name = w["display_name"] if w else worker_id
    blockers = []
    for e in filter(OPEN, exceptions):
        s1 = e["stage_impact"]["stage1_wages"]
        if e["category"] == "coverage_gap" and s1 != "none":
            blockers += _cov_blocker(e)
        elif e["entity_refs"].get("worker_id") == worker_id and s1 in ("blocks_worker", "blocks_item"):
            blockers.append(_exc_blocker(e))
    blockers = _dedupe(blockers)
    wk = weekly_minutes([e for e in cycle_entries(snapshot) if e["worker_id"] == worker_id],
                        snapshot["cycle"]["workweeks"])
    mins = {k: v.get(worker_id) for k, v in wk.items()}
    gross = worker_gross_cents(snapshot, worker_id)
    known = [m for m in mins.values() if m is not None]
    scope = f"{name}: " + ", ".join(f"wk {k} {('unknown' if v is None else str(v) + ' min')}" for k, v in mins.items())
    unknown = gross is None or len(known) != len(mins)
    if unknown and not blockers:
        # never ready with an unknown amount, even if the related case was marked resolved
        blockers.append({"code": "amount_unknown:wages", "label": f"{name}: gross wages cannot be computed",
                         "exception_id": None})
    return _readiness("blocked" if blockers else "ready", scope, blockers, unknown, now)


def stage1_detail(snapshot: dict, exceptions: list[dict], now=None) -> tuple[dict, dict[str, dict]]:
    """(stage1 Readiness, {worker_id: Readiness}) for workers with in-cycle time."""
    active = sorted({e["worker_id"] for e in cycle_entries(snapshot)})
    workers = {wid: worker_readiness(snapshot, wid, exceptions, now) for wid in active}
    return _stage1_from_workers(workers, exceptions, now), workers


def _stage1_from_workers(workers: dict[str, dict], exceptions: list[dict], now=None) -> dict:
    ready = [w for w, r in workers.items() if r["state"] == "ready"]
    blockers = _dedupe([b for r in workers.values() for b in r["blockers"]])
    excluded = sum(1 for e in exceptions if e["category"] == "unassigned_time" and OPEN(e))
    n = len(workers)
    state = "pending" if not n else "ready" if len(ready) == n else "partial" if ready else "blocked"
    scope = f"review-ready for {len(ready)} of {n} workers; {n - len(ready)} unresolved"
    if excluded:
        scope += f"; {excluded} out-of-cycle entr{'y' if excluded == 1 else 'ies'} excluded"
    return _readiness(state, scope, blockers, any(r["unknown_amount"] for r in workers.values()), now)


def stage1_readiness(snapshot_or_workers, exceptions: list[dict], now=None) -> dict:
    """Stage 1 Readiness. Preferred: pass the (corrected) snapshot dict. Legacy form: a list of Worker dicts,
    which can only use exception state (no time/rate data), so amounts are reported unknown and a worker
    with no blocking exception is still blocked by amount_unknown:wages. Prefer cycle_readiness()."""
    if isinstance(snapshot_or_workers, dict):
        return stage1_detail(snapshot_or_workers, exceptions, now)[0]
    workers = {}
    for w in snapshot_or_workers:
        wid = w["id"]
        blockers = [_exc_blocker(e) for e in filter(OPEN, exceptions)
                    if e["entity_refs"].get("worker_id") == wid
                    and e["stage_impact"]["stage1_wages"] in ("blocks_worker", "blocks_item")]
        blockers += [b for e in filter(OPEN, exceptions) if e["category"] == "coverage_gap"
                     and e["stage_impact"]["stage1_wages"] != "none" for b in _cov_blocker(e)]
        if not blockers:
            blockers = [{"code": "amount_unknown:wages", "label": "time entries not supplied to readiness",
                         "exception_id": None}]
        workers[wid] = _readiness("blocked", w.get("display_name", wid), blockers, True, now)
    return _stage1_from_workers(workers, exceptions, now)


# ------------------------------------------------------------------ job economics helpers
def job_labor_cents(snapshot: dict, job_id: str) -> int | None:
    workers = {w["id"]: w for w in snapshot.get("workers", [])}
    total = Decimal(0)
    for e in cycle_entries(snapshot):
        if e.get("job_id") != job_id:
            continue
        part = gross_wages_exact(e.get("duration_minutes"), verified_rate_cents(workers.get(e["worker_id"]), e["date"]))
        if part is None:
            return None
        total += part
    return to_cents(total)


def eligible_receipts_cents(snapshot: dict) -> int:
    """Company receipts collected in this cycle. Tips excluded (T12). Failed/pending excluded. A receipt
    moved to another cycle is excluded only when that allocation is FINALIZED with evidence (T19)."""
    c = snapshot["cycle"]
    total = 0
    for r in snapshot.get("receipts", []):
        if r.get("kind") in ("tip", "refund") or r.get("status") != "succeeded":
            continue
        if not in_period(r["payment_date"], c["period_start"], c["period_end"]):
            continue
        alloc = r.get("cycle_allocation") or {}
        moved = alloc.get("allocated_cycle_id") not in (None, c["id"])
        if moved and alloc.get("state") == "finalized" and alloc.get("finalization_evidence"):
            continue
        total += r["amount_cents"]
    return total


def _job_touching_exceptions(snapshot: dict, job_id: str, exceptions: list[dict]) -> list[dict]:
    """Open exceptions that can change job_id's full-job profit."""
    entries = {e["id"]: e for e in snapshot.get("time_entries", [])}
    costs = {c["id"]: c for c in snapshot.get("costs", [])}
    jobs = {j["id"]: j for j in snapshot.get("jobs", [])}
    labor_workers = {e["worker_id"] for e in cycle_entries(snapshot) if e.get("job_id") == job_id}
    out = []
    for e in filter(OPEN, exceptions):
        refs, cat = e["entity_refs"], e["category"]
        if cat in ("coverage_gap", "unassigned_time"):
            continue
        hit = False
        if job_id in refs.get("job_ids", []) and cat != "offsite_link":
            hit = True
        if cat == "offsite_link":  # unlinked off-site work may roll up to this job
            hit = any(jobs.get(j, {}).get("parent_job_id") in (None, job_id) for j in refs.get("job_ids", []))
            hit = hit and job_id not in refs.get("job_ids", [])
        if e["stage_impact"]["stage2_costs"] != "none":
            for tid in refs.get("time_entry_ids", []):
                te = entries.get(tid)
                if te and te.get("job_id") in (None, job_id):
                    hit = True
            for cid in refs.get("cost_ids", []):
                c = costs.get(cid)
                if c and (not c.get("job_allocations") or any(a["job_id"] == job_id for a in c["job_allocations"])):
                    hit = True
        if cat in ("rate_unconfirmed", "identity") and refs.get("worker_id") in labor_workers:
            hit = True  # labor cost on this job is unknown
        if hit:
            out.append(e)
    return out


def _cost_coverage_blockers(exceptions: list[dict]) -> list[dict]:
    out = []
    for e in filter(OPEN, exceptions):
        if e["category"] == "coverage_gap" and e["stage_impact"]["stage2_costs"] != "none":
            out += _cov_blocker(e)
    return out


def _has_prior_history(snapshot: dict, job_id: str) -> bool:
    start = date.fromisoformat(snapshot["cycle"]["period_start"])
    return any(r["job_id"] == job_id and date.fromisoformat(r["payment_date"]) < start
               for r in snapshot.get("receipts", []))


# ------------------------------------------------------------------ Stage 2 items
def quote_item(snapshot, job, exceptions, policies, now=None) -> dict:
    jid = job["id"]
    qpol = policies.get("quote_pool")
    confirmed = [q["worker_id"] for q in job.get("quoter_candidates", []) if q.get("basis", "").startswith("confirmed")]
    item = {"id": f"ci_quote_{jid}", "cycle_id": snapshot["cycle"]["id"], "kind": "quote_commission",
            "worker_id": None, "job_id": jid, "policy_version": snapshot["cycle"].get("policy_version"),
            "inputs": {"eligible_profit_cents": None, "quoters": confirmed, "prior_paid_cents": None},
            "computed": None, "obligation_ids": [], "provenance": snapshot.get("provenance", "synthetic")}
    if not job.get("final_payment_verified") or job.get("status") != "complete":
        item["readiness"] = _readiness("not_meaningful", f"{job['display_name']}: no verified final payment",
                                       [{"code": "policy_missing:final_payment",
                                         "label": "Final payment not verified (SOP rule)", "exception_id": None}],
                                       True, now)
        return item
    blockers = []
    if not qpol or qpol.get("status") != "approved":
        blockers.append({"code": "policy_missing:O03", "label": "Quote pool policy not approved", "exception_id": None})
    blockers += [_exc_blocker(e) for e in _job_touching_exceptions(snapshot, jid, exceptions)]
    blockers += _cost_coverage_blockers(exceptions)
    if _has_prior_history(snapshot, jid):
        blockers.append({"code": "coverage:historical_labor",
                         "label": "Full-job labor before this cycle is not in the snapshot", "exception_id": None})
    profit = None
    if not blockers:
        labor = job_labor_cents(snapshot, jid)
        job_costs = sum_known(a["amount_cents"] for c in snapshot.get("costs", [])
                              if c.get("included_in_calc") for a in c.get("job_allocations", []) if a["job_id"] == jid)
        if job.get("adjusted_invoice_cents") is not None and labor is not None and job_costs is not None:
            profit = job["adjusted_invoice_cents"] - labor - job_costs
            item["inputs"]["eligible_profit_cents"] = profit
            try:
                item["computed"] = quote_pool(profit, confirmed, {}, final_payment_verified=True, policy=qpol)
                blockers += item["computed"]["blockers"]
            except CalcBlocked as ex:
                blockers.append(ex.as_blocker())
        else:
            blockers.append({"code": "component_unknown:job_profit", "label": "Job profit inputs unknown",
                             "exception_id": None})
    state = "ready" if not blockers else "pending"
    item["readiness"] = _readiness(state, f"{job['display_name']}; quoters confirmed: {len(confirmed)}",
                                   _dedupe(blockers), item["computed"] is None, now)
    return item


def marketing_item(snapshot, job, exceptions, policies, now=None) -> dict:
    jid = job["id"]
    rule = ((policies.get("marketing") or {}).get("job_rules") or {}).get(jid)
    blockers = [] if rule else [{"code": "policy_missing:O04", "label": "Marketing rule absent for this job (O04)",
                                 "exception_id": None}]
    if rule:  # a documented job rule exists; computing it is out of scope for the synthetic cycle
        blockers.append({"code": "unsupported:marketing_calc", "label": "Marketing calculation not implemented",
                         "exception_id": None})
    return {"id": f"ci_marketing_{jid}", "cycle_id": snapshot["cycle"]["id"], "kind": "marketing",
            "worker_id": None, "job_id": jid, "policy_version": snapshot["cycle"].get("policy_version"),
            "inputs": {"rule": rule}, "computed": None, "obligation_ids": [],
            "provenance": snapshot.get("provenance", "synthetic"),
            "readiness": _readiness("pending", f"{job['display_name']}; job-specific marketing rule "
                                    f"{'documented' if rule else 'absent'}", blockers, True, now)}


def tip_item(snapshot, receipt, exceptions, policies, now=None) -> dict:
    blockers = []
    if (policies.get("tip_rule") or {}).get("status") != "approved":
        blockers.append({"code": "policy_missing:O07", "label": "Tip eligibility/allocation rule unresolved (O07)",
                         "exception_id": None})
    paid = [o for o in snapshot.get("obligations", []) if o.get("kind") == "tip" and o.get("job_id") == receipt["job_id"]]
    if not paid or any(o.get("balance_cents") is None for o in paid):
        blockers.append({"code": "prior_payment_unknown", "label": "Prior tip payout not verified",
                         "exception_id": None})
    return {"id": f"ci_tip_{receipt['id']}", "cycle_id": snapshot["cycle"]["id"], "kind": "tip",
            "worker_id": None, "job_id": receipt["job_id"], "policy_version": snapshot["cycle"].get("policy_version"),
            "inputs": {"tip_cents": receipt["amount_cents"], "receipt_id": receipt["id"]}, "computed": None,
            "obligation_ids": [o["id"] for o in paid], "provenance": snapshot.get("provenance", "synthetic"),
            "readiness": _readiness("pending" if blockers else "ready",
                                    f"Tip {receipt['amount_cents']} cents on {receipt['job_id']}; excluded from company receipts",
                                    blockers, receipt.get("amount_cents") is None, now)}


def manager_pool_item(snapshot, exceptions, policies, stage1, commission_items, now=None) -> dict:
    blockers = []
    if (policies.get("overhead_allocation") or {}).get("status") != "approved":
        blockers.append({"code": "policy_missing:O05", "label": "Overhead allocation method unresolved (O05)",
                         "exception_id": None})
    mp = policies.get("manager_split") or {}
    if mp.get("status") != "approved" or mp.get("requires_resolution"):
        unresolved = ", ".join(mp.get("requires_resolution") or []) or f"status {mp.get('status')}"
        blockers.append({"code": "policy_missing:O06", "label": f"Manager allocation unresolved: {unresolved} (O06)",
                         "exception_id": None})
    blockers += _cost_coverage_blockers(exceptions)
    if stage1["state"] != "ready":
        blockers.append({"code": "stage1_exposure", "label": f"Unresolved wage exposure ({stage1['scope']})",
                         "exception_id": None})
    for r in snapshot.get("receipts", []):
        alloc = r.get("cycle_allocation") or {}
        if alloc.get("state") == "proposed":
            blockers.append({"code": f"allocation_provisional:{r['id']}",
                             "label": f"{r['id']} allocation to {alloc.get('allocated_cycle_id')} proposed, not finalized (T19)",
                             "exception_id": None})
    if any(i["readiness"]["state"] == "pending" for i in commission_items):
        blockers.append({"code": "commissions_pending", "label": "Commission amounts not final", "exception_id": None})
    for e in filter(OPEN, exceptions):
        if e["category"] != "coverage_gap" and e["stage_impact"]["stage2_costs"] != "none":
            blockers.append(_exc_blocker(e))
    return {"id": "ci_manager_pool", "cycle_id": snapshot["cycle"]["id"], "kind": "manager_pool",
            "worker_id": None, "job_id": None, "policy_version": snapshot["cycle"].get("policy_version"),
            "inputs": {"split_source": "policy file (placeholders in fixtures)"}, "computed": None,
            "obligation_ids": [], "provenance": snapshot.get("provenance", "synthetic"),
            "readiness": _readiness("blocked" if blockers else "ready",
                                    "Cycle pool provisional; final distributions blocked" if blockers else "Cycle pool ready",
                                    _dedupe(blockers), True, now)}


def readiness_for(item: dict, exceptions: list[dict], policies: dict | None = None, snapshot: dict | None = None,
                  now=None) -> dict:
    """Recompute one item's Readiness. Needs the snapshot for job/receipt context."""
    if snapshot is None:
        raise ValueError("snapshot required")
    pol = _policies(snapshot, policies)
    kind = item["kind"]
    if kind == "wages":
        return worker_readiness(snapshot, item["worker_id"], exceptions, now)
    if kind == "quote_commission":
        job = next(j for j in snapshot["jobs"] if j["id"] == item["job_id"])
        return quote_item(snapshot, job, exceptions, pol, now)["readiness"]
    if kind == "marketing":
        job = next(j for j in snapshot["jobs"] if j["id"] == item["job_id"])
        return marketing_item(snapshot, job, exceptions, pol, now)["readiness"]
    if kind == "tip":
        rcpt = next(r for r in snapshot["receipts"] if r["id"] == item["inputs"]["receipt_id"])
        return tip_item(snapshot, rcpt, exceptions, pol, now)["readiness"]
    if kind == "manager_pool":
        return cycle_readiness(snapshot, exceptions, policies, now)["items_by_id"]["ci_manager_pool"]["readiness"]
    raise ValueError(f"unknown item kind {kind!r}")


def cycle_readiness(snapshot: dict, exceptions: list[dict], policies: dict | None = None, now=None) -> dict:
    """Everything the board needs: {"stage1", "workers", "items", "items_by_id", "stage2_summary"}.
    `policies` (e.g. the private policy file) overrides snapshot["policies"] key by key."""
    pol = _policies(snapshot, policies)
    stage1, workers = stage1_detail(snapshot, exceptions, now)
    revenue_jobs = {r["job_id"] for r in snapshot.get("receipts", []) if r.get("kind") != "tip"}
    quote_items = [quote_item(snapshot, j, exceptions, pol, now) for j in snapshot.get("jobs", [])
                   if j.get("adjusted_invoice_cents") is not None or j["id"] in revenue_jobs]
    marketing = [marketing_item(snapshot, j, exceptions, pol, now) for j in snapshot.get("jobs", [])
                 if j.get("status") == "complete" and j.get("final_payment_verified")]
    tips = [tip_item(snapshot, r, exceptions, pol, now) for r in snapshot.get("receipts", []) if r.get("kind") == "tip"]
    mgr = manager_pool_item(snapshot, exceptions, pol, stage1, quote_items + marketing, now)
    items = quote_items + marketing + tips + [mgr]
    return {"stage1": stage1, "workers": workers, "items": items, "items_by_id": {i["id"]: i for i in items},
            "stage2_summary": stage2_summary(items)}


def stage2_summary(items: list[dict]) -> str:
    """Item-by-item summary; never rolls up to 'complete'."""
    parts = []
    for i in items:
        r = i["readiness"]
        parts.append(f"{i['id']}: {r['state']}" + (f" ({len(r['blockers'])} blockers)" if r["blockers"] else ""))
    return "; ".join(parts)
