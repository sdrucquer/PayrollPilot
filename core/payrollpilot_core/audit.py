"""Deterministic audit rules: snapshot dict -> list of CONTRACTS `Exception` dicts. No LLM, no IO.

Rules never trim hours, assume breaks, or substitute scheduled time for actual time. Unknown dollar
impact is None. Entries outside the cycle boundaries are excluded from every in-cycle rule and
reported (T27), never swept in. Exception ids are a hash of (category, entity refs), so re-running
the audit yields identical ids.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .ids import exception_id
from .money import gross_wages
from .time import find_duplicates, find_overlaps, format_minutes, in_period

DEFAULT_LONG_SHIFT_MINUTES = 480  # SOP review threshold (PRD 6.2); review only, never a cap


def _refs(worker_id=None, time_entry_ids=(), job_ids=(), cost_ids=(), coverage=None) -> dict:
    r = {"worker_id": worker_id, "time_entry_ids": sorted(time_entry_ids), "job_ids": sorted(job_ids),
         "cost_ids": sorted(cost_ids)}
    if coverage:
        r["coverage"] = sorted(coverage)
    return r


def applicable_rate(worker: dict, on: str) -> dict | None:
    """The worker's rate row effective on the given date, or None."""
    d = date.fromisoformat(on)
    for r in worker.get("rates", []):
        start = date.fromisoformat(r["effective_from"])
        end = date.fromisoformat(r["effective_to"]) if r.get("effective_to") else None
        if start <= d and (end is None or d <= end):
            return r
    return None


def verified_rate_cents(worker: dict | None, on: str) -> int | None:
    if worker is None or worker.get("identity_status") != "verified":
        return None
    r = applicable_rate(worker, on)
    if r is None or r.get("status") != "verified":
        return None
    return r.get("rate_cents_per_hour")


class _Builder:
    def __init__(self, snapshot: dict, now: str | None):
        self.snap = snapshot
        self.cycle = snapshot["cycle"]
        self.now = now or snapshot.get("captured_at")
        self.workers = {w["id"]: w for w in snapshot.get("workers", [])}
        self.jobs = {j["id"]: j for j in snapshot.get("jobs", [])}
        self.default_prov = "real" if snapshot.get("provenance") == "real" else "synthetic"
        self.out: dict[str, dict] = {}

    def add(self, category: str, refs: dict, *, title: str, observed: str, expected: str, evidence: list,
            stage1: str, stage2: str, respondent: str, next_action: str, dollars: int | None = None,
            records: list[dict] = ()) -> None:
        eid = exception_id(category, refs)
        if eid in self.out:
            return
        seeded = any(r.get("provenance") == "seeded_issue" for r in records)
        self.out[eid] = {
            "id": eid, "cycle_id": self.cycle["id"], "category": category, "title": title,
            "observed": observed, "expected": expected,
            "evidence": [e for e in evidence if e],
            "entity_refs": refs,
            "stage_impact": {"stage1_wages": stage1, "stage2_costs": stage2},
            "dollars_affected_cents": dollars, "intended_respondent_role": respondent,
            "state": "detected", "next_action": next_action, "owner_agent": "audit",
            "message_ids": [], "resolution_id": None,
            "provenance": "seeded_issue" if seeded else self.default_prov,
            "created_at": self.now, "updated_at": self.now,
        }

    def entry_cost(self, e: dict) -> int | None:
        return gross_wages(e.get("duration_minutes"), verified_rate_cents(self.workers.get(e["worker_id"]), e["date"]))

    def wname(self, wid: str | None) -> str:
        w = self.workers.get(wid or "")
        return w["display_name"] if w else (wid or "unknown worker")

    def jname(self, jid: str | None) -> str:
        j = self.jobs.get(jid or "")
        return j["display_name"] if j else (jid or "no job")


def run_audit(snapshot: dict, now: str | None = None) -> list[dict]:
    """Run every deterministic rule over one cycle snapshot. Output sorted by (category, id)."""
    b = _Builder(snapshot, now)
    cyc = b.cycle
    policies = snapshot.get("policies", {})
    long_shift = (policies.get("long_shift_review_minutes") or {}).get("threshold_minutes", DEFAULT_LONG_SHIFT_MINUTES)

    all_entries = snapshot.get("time_entries", [])
    entries = [e for e in all_entries if in_period(e["date"], cyc["period_start"], cyc["period_end"])]
    by_id = {e["id"]: e for e in all_entries}

    # ---- coverage gaps (T13): incomplete reads are never treated as complete
    for cov in cyc.get("coverage", []):
        if not cov.get("complete", False):
            key = f"{cov['system']}:{cov['dataset']}"
            b.add("coverage_gap", _refs(coverage=[key]),
                  title=f"{cov['system']}/{cov['dataset']} coverage incomplete ({cov.get('incomplete_reason') or 'unknown'})",
                  observed=f"{cov.get('record_count')} records read; complete=false, reason={cov.get('incomplete_reason')}",
                  expected="complete coverage for the cycle range, or the gap disclosed as a blocker",
                  evidence=[{"system": cov["system"], "record_id": f"coverage:{cov['dataset']}", "url": None,
                             "captured_at": cov.get("captured_at"), "snapshot_id": cov.get("snapshot_id")}],
                  stage1="blocks_item" if cov["dataset"] in ("time_entries", "workers", "rates") else "none",
                  stage2="job_costing" if cov["dataset"] in ("expenses", "payments", "jobs") else "none",
                  respondent="owner", next_action=f"confirm or restore access to {key}")

    # ---- approval-queue trap (T27): out-of-cycle entries excluded and reported
    for e in all_entries:
        if e in entries:
            continue
        b.add("unassigned_time", _refs(e["worker_id"], [e["id"]]),
              title=f"{'Unapproved e' if not e.get('approved_in_source') else 'E'}ntry dated {e['date']} is outside the cycle; "
                    f"excluded, prior payment {e.get('paid_status', 'unknown')}",
              observed=f"{b.wname(e['worker_id'])} {format_minutes(e.get('duration_minutes'))} on {e['date']}, "
                       f"approved_in_source={e.get('approved_in_source')}, paid_status={e.get('paid_status')}",
              expected=f"only entries dated {cyc['period_start']}..{cyc['period_end']} belong to this cycle; "
                       "unapproved does not mean unpaid",
              evidence=[e.get("source_ref"), e.get("paid_ref")], stage1="none", stage2="none",
              respondent="owner", next_action="owner checks prior payroll for this entry; not added to this cycle",
              records=[e])

    # ---- per-entry rules
    for e in entries:
        wid, dur = e["worker_id"], e.get("duration_minutes")
        is_open = bool(e.get("open_timer")) or (e.get("start") and not e.get("end")) or dur is None
        if is_open:
            b.add("open_timer", _refs(wid, [e["id"]]),
                  title=f"Timer on {e['date']} still open; duration unknown",
                  observed=f"{b.wname(wid)} started {e.get('start')} with no end; duration_minutes=null",
                  expected="every paid shift has an end time",
                  evidence=[e.get("source_ref")], stage1="blocks_worker", stage2="job_costing",
                  respondent="ops_lead", next_action="ask ops lead for the actual end time", records=[e])
            continue
        if not e.get("job_id"):
            b.add("missing_job", _refs(wid, [e["id"]]),
                  title=f"Shift on {e['date']} ({format_minutes(dur)}) has no job assigned",
                  observed=f"{b.wname(wid)} {format_minutes(dur)} ({dur} min) logged, job empty",
                  expected="every paid shift maps to a job",
                  evidence=[e.get("source_ref")], stage1="none", stage2="job_costing",
                  respondent="ops_lead", next_action="ask ops lead which job this time belongs to",
                  dollars=b.entry_cost(e), records=[e])
        if dur > long_shift:
            b.add("long_shift", _refs(wid, [e["id"]]),
                  title=f"Shift on {e['date']} is {format_minutes(dur)} (over {format_minutes(long_shift)} review threshold)",
                  observed=f"{b.wname(wid)} {e.get('start')} to {e.get('end')} = {dur} min",
                  expected=f"shifts over {long_shift} min are reviewed; hours are never trimmed or breaks assumed",
                  evidence=[e.get("source_ref")], stage1="blocks_worker", stage2="none",
                  respondent="ops_lead", next_action="ask ops lead to confirm the actual hours worked", records=[e])
        sched_job = e.get("scheduled_job_id")
        if sched_job and e.get("job_id") and sched_job != e["job_id"]:
            if e.get("paid_status") == "paid_prior_cycle":
                b.add("already_paid_allocation", _refs(wid, [e["id"]], [e["job_id"], sched_job]),
                      title=f"Already-paid shift on {e['date']} is on {b.jname(e['job_id'])} but scheduled on {b.jname(sched_job)}",
                      observed=f"{b.wname(wid)} {format_minutes(dur)} paid in a prior run, logged to {e['job_id']}, scheduled on {sched_job}",
                      expected="allocation corrections change job costing only; no new wage payment",
                      evidence=[e.get("source_ref"), e.get("paid_ref")], stage1="none", stage2="job_costing",
                      respondent="ops_lead", next_action="ask ops lead which job the shift was actually worked on",
                      dollars=b.entry_cost(e), records=[e])
            else:
                b.add("schedule_mismatch", _refs(wid, [e["id"]], [e["job_id"], sched_job]),
                      title=f"Shift on {e['date']} logged to {b.jname(e['job_id'])} but scheduled on {b.jname(sched_job)}",
                      observed=f"logged job {e['job_id']}, scheduled job {sched_job}",
                      expected="schedule corroborates but does not prove the job",
                      evidence=[e.get("source_ref")], stage1="none", stage2="job_costing",
                      respondent="ops_lead", next_action="ask ops lead which job was worked", records=[e])
        sched = e.get("scheduled_minutes")
        if sched is not None and sched != dur:
            b.add("schedule_mismatch", _refs(wid, [e["id"]]),
                  title=f"Logged {dur}m vs scheduled {sched}m on {e['date']}",
                  observed=f"{b.wname(wid)} logged {format_minutes(dur)}, schedule {format_minutes(sched)}",
                  expected="actual work stands unless corrected with evidence; schedule never replaces it",
                  evidence=[e.get("source_ref")], stage1="blocks_worker", stage2="none",
                  respondent="ops_lead", next_action="ask ops lead to confirm actual hours", records=[e])

    for ids in find_duplicates(entries):
        recs = [by_id[i] for i in ids]
        b.add("duplicate_time", _refs(recs[0]["worker_id"], ids),
              title=f"Identical entries on {recs[0]['date']} (possible duplicate)",
              observed=f"{len(ids)} entries with same worker, job, start, end: {', '.join(ids)}",
              expected="each worked interval recorded once",
              evidence=[r.get("source_ref") for r in recs], stage1="blocks_worker", stage2="job_costing",
              respondent="ops_lead", next_action="ask ops lead whether this is a duplicate", records=recs)

    for a, c, minutes in find_overlaps(entries):
        ra, rc = by_id[a], by_id[c]
        b.add("overlap", _refs(ra["worker_id"], [a, c]),
              title=f"Two entries on {ra['date']} overlap by {minutes} minutes",
              observed=f"{a} {ra.get('start')}-{ra.get('end')} and {c} {rc.get('start')}-{rc.get('end')}",
              expected="a worker's entries do not overlap",
              evidence=[ra.get("source_ref"), rc.get("source_ref")], stage1="blocks_worker", stage2="job_costing",
              respondent="ops_lead", next_action="ask ops lead which interval is correct", records=[ra, rc])

    # ---- worker identity and rates (only workers with in-cycle time)
    active = sorted({e["worker_id"] for e in entries})
    for wid in active:
        w = b.workers.get(wid)
        if w is None:
            b.add("identity", _refs(wid), title=f"Time logged by unknown worker {wid}",
                  observed="no worker record in snapshot", expected="every worker maps to a verified identity",
                  evidence=[], stage1="blocks_worker", stage2="none", respondent="owner",
                  next_action="owner identifies this worker")
            continue
        if w.get("identity_status") != "verified":
            b.add("identity", _refs(wid),
                  title=f"{w['display_name']} identity is {w.get('identity_status')}; reconcile before merging hours",
                  observed=f"identity_status={w.get('identity_status')}",
                  expected="one verified identity across Jobber and Gusto",
                  evidence=[w.get("jobber_ref"), w.get("gusto_ref")], stage1="blocks_worker", stage2="none",
                  respondent="owner", next_action="owner confirms which profile is current", records=[w])
        dates = sorted({e["date"] for e in entries if e["worker_id"] == wid})
        bad = [d for d in dates if (r := applicable_rate(w, d)) is None or r.get("status") != "verified"
               or r.get("rate_cents_per_hour") is None]
        if bad or w.get("payment_route") == "unknown":
            b.add("rate_unconfirmed", _refs(wid),
                  title=f"{w['display_name']} rate{' and payment route' if w.get('payment_route') == 'unknown' else ''} unconfirmed",
                  observed=f"no verified effective rate for {len(bad)} work date(s); payment_route={w.get('payment_route')}",
                  expected="verified work-date-effective rate and payment route (owner confirms; never inferred)",
                  evidence=[r.get("evidence") for r in w.get("rates", [])] + [w.get("jobber_ref")],
                  stage1="blocks_worker", stage2="none", respondent="owner",
                  next_action="ask owner to confirm rate and payment route", records=[w])

    # ---- costs (one economic identity per underlying cost)
    for c in snapshot.get("costs", []):
        reps = [r for r in c.get("representations", []) if r.get("kind") != "estimate"]
        amounts = {r.get("amount_cents") for r in reps}
        alloc_sum = sum(a.get("amount_cents") or 0 for a in c.get("job_allocations", []))
        alloc_mismatch = (c.get("allocated") and c.get("amount_cents") is not None
                          and c.get("job_allocations") and alloc_sum != c["amount_cents"])
        if c.get("conflict") == "amount_mismatch" or len(amounts) > 1 or alloc_mismatch:
            b.add("cost_conflict", _refs(cost_ids=[c["id"]]),
                  title=f"{c['description'].capitalize()}: source amounts differ" if not alloc_mismatch
                  else f"{c['description'].capitalize()}: job allocations do not sum to the cost",
                  observed="; ".join(f"{r['kind']} {r.get('amount_cents')}" for r in reps)
                  + (f"; allocations sum {alloc_sum} vs {c.get('amount_cents')}" if alloc_mismatch else ""),
                  expected="one amount per economic cost, counted once; allocations reconcile to the total",
                  evidence=[r.get("source_ref") for r in c.get("representations", [])],
                  stage1="none", stage2="job_costing", respondent="ops_lead",
                  next_action="ask ops lead for the correct amount and evidence", dollars=c.get("amount_cents"),
                  records=[c])
        elif not c.get("categorized") or not c.get("allocated"):
            b.add("unmatched_cost", _refs(cost_ids=[c["id"]]),
                  title=f"{c['description'].capitalize()} ({c.get('cost_date')}) has no "
                        f"{'job or category' if not c.get('categorized') and not c.get('allocated') else ('job' if not c.get('allocated') else 'category')}",
                  observed=f"categorized={c.get('categorized')}, allocated={c.get('allocated')}, amount {c.get('amount_cents')}",
                  expected="every cost is categorized and allocated (not guessed from vendor name)",
                  evidence=[r.get("source_ref") for r in c.get("representations", [])],
                  stage1="none", stage2="job_costing", respondent="ops_lead",
                  next_action="ask ops lead which job and category this purchase belongs to",
                  dollars=c.get("amount_cents"), records=[c])

    # ---- jobs: off-site links and quote attribution
    labor_jobs = {e.get("job_id") for e in entries}
    cost_jobs = {a["job_id"] for c in snapshot.get("costs", []) for a in c.get("job_allocations", [])}
    revenue_jobs = {r["job_id"] for r in snapshot.get("receipts", [])}
    for j in snapshot.get("jobs", []):
        jid = j["id"]
        if (j.get("parent_job_id") is None and j.get("adjusted_invoice_cents") is None and jid not in revenue_jobs
                and (jid in labor_jobs or jid in cost_jobs)):
            b.add("offsite_link", _refs(job_ids=[jid]),
                  title=f"{j['display_name']} has labor or costs but no revenue and no parent job link",
                  observed="parent_job_id=null, no invoice, no receipts; labor/costs recorded",
                  expected="off-site work links to the parent job whose economics it affects",
                  evidence=[j.get("source_ref")], stage1="none", stage2="job_costing", respondent="ops_lead",
                  next_action="ask ops lead which parent job this off-site work belongs to", records=[j])
        confirmed = [q for q in j.get("quoter_candidates", []) if q.get("basis", "").startswith("confirmed")]
        if j.get("status") == "complete" and j.get("final_payment_verified") and not confirmed:
            cands = ", ".join(f"{q['worker_id']} ({q['basis']})" for q in j.get("quoter_candidates", [])) or "none"
            b.add("quote_attribution", _refs(job_ids=[jid]),
                  title=f"{j['display_name']} quoter unconfirmed (candidates: {cands})",
                  observed=f"quoter candidates: {cands}",
                  expected="actual quoter(s) confirmed; the salesperson field alone is candidate evidence",
                  evidence=[j.get("source_ref")], stage1="none", stage2="commission", respondent="ops_lead",
                  next_action="ask ops lead who performed the in-person quote", records=[j])

    return sorted(b.out.values(), key=lambda x: (x["category"], x["id"]))


def audit_key(exc: dict) -> tuple:
    """Order-insensitive comparison key: (category, entity refs)."""
    refs = exc["entity_refs"]
    return (exc["category"], refs.get("worker_id"), tuple(refs.get("time_entry_ids", [])),
            tuple(refs.get("job_ids", [])), tuple(refs.get("cost_ids", [])), tuple(refs.get("coverage", [])))


def summarize(exceptions: list[dict]) -> dict[str, Any]:
    by_cat: dict[str, int] = {}
    for e in exceptions:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
    return {"count": len(exceptions), "by_category": dict(sorted(by_cat.items()))}
