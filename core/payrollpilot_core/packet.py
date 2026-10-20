"""Internal review packet (FR-22): period, identities (display names only), earnings, calc version, evidence,
scoped readiness, reconciliation figures and a workbook reference placeholder. Pure; no IO.

Preferred call: build_packet(snapshot=view, exceptions=excs, corrections=corrs, policies=private_or_None).
Legacy positional form (cycle, workers, entries, items, exceptions, corrections) is accepted; without
receipts/costs/jobs those ledgers are reported as not supplied, never as zero.
"""
from __future__ import annotations

from . import CALC_VERSION, CONTRACT_VERSION
from .audit import applicable_rate, run_audit
from .calc import cycle_profit_bridge, labor_revenue_ratios
from .ids import content_hash
from .money import sum_known
from .readiness import (
    cycle_entries,
    cycle_readiness,
    eligible_receipts_cents,
    job_labor_cents,
    worker_gross_cents,
)
from .time import weekly_minutes


def _snapshot_from_parts(cycle, workers, entries) -> dict:
    return {"snapshot_id": None, "captured_at": None, "provenance": (cycle or {}).get("provenance", "synthetic"),
            "cycle": cycle, "workers": workers or [], "time_entries": entries or [], "jobs": [], "receipts": [],
            "costs": [], "obligations": [], "policies": {}, "_partial": True}


def build_packet(cycle: dict | None = None, workers: list | None = None, entries: list | None = None,
                 items: list | None = None, exceptions: list | None = None, corrections: list | None = None, *,
                 snapshot: dict | None = None, policies: dict | None = None, now: str | None = None) -> dict:
    if snapshot is None:
        if cycle is not None and "cycle" in cycle:  # a snapshot passed positionally
            snapshot = cycle
        else:
            snapshot = _snapshot_from_parts(cycle, workers, entries)
    partial = bool(snapshot.get("_partial"))
    cyc = snapshot["cycle"]
    excs = list(exceptions) if exceptions is not None else run_audit(snapshot, now=now)
    corrs = list(corrections or [])
    ready = cycle_readiness(snapshot, excs, policies, now)

    # ---- earnings (Stage 1)
    entries_in = cycle_entries(snapshot)
    weeks = cyc["workweeks"]
    wk = weekly_minutes(entries_in, weeks)
    earnings = []
    for wid, r in ready["workers"].items():
        w = next((x for x in snapshot["workers"] if x["id"] == wid), {"id": wid, "display_name": wid, "rates": []})
        dates = sorted({e["date"] for e in entries_in if e["worker_id"] == wid})
        rates = []
        for d in dates:
            rr = applicable_rate(w, d) if w.get("rates") else None
            seg = {"effective_from": rr["effective_from"], "rate_cents_per_hour": rr.get("rate_cents_per_hour"),
                   "category": rr.get("category"), "status": rr.get("status")} if rr else None
            if seg not in rates:
                rates.append(seg)
        earnings.append({
            "worker_id": wid, "display_name": w.get("display_name", wid), "payment_route": w.get("payment_route"),
            "weekly_minutes": {k: v.get(wid) for k, v in wk.items()},
            "rates": rates, "gross_new_cents": worker_gross_cents(snapshot, wid),
            "earnings_category": "regular_hourly", "readiness": r,
            "prior_obligations": [o["id"] for o in snapshot.get("obligations", []) if o.get("worker_id") == wid],
        })
    ready_gross = [e["gross_new_cents"] for e in earnings if e["readiness"]["state"] == "ready"]

    # ---- reconciliation figures
    receipts = snapshot.get("receipts", [])
    tips = sum(r["amount_cents"] for r in receipts if r.get("kind") == "tip" and r.get("status") == "succeeded")
    included_costs = [c for c in snapshot.get("costs", []) if c.get("included_in_calc")]
    unincluded = [c for c in snapshot.get("costs", []) if not c.get("included_in_calc")]
    direct_expenses = None if (unincluded or partial) else sum_known(c.get("amount_cents") for c in included_costs)
    stage1_total = sum_known(e["gross_new_cents"] for e in earnings)
    revenue = None if partial else eligible_receipts_cents(snapshot)
    bridge = cycle_profit_bridge([
        {"key": "eligible_receipts", "label": "Eligible allocated receipts", "sign": 1, "amount_cents": revenue},
        {"key": "direct_expenses", "label": "Approved direct expenses", "sign": -1, "amount_cents": direct_expenses},
        {"key": "gross_labor", "label": "Gross labor", "sign": -1, "amount_cents": stage1_total},
        {"key": "employer_labor_costs", "label": "Employer labor costs", "sign": -1, "amount_cents": None},
        {"key": "overhead", "label": "Overhead", "sign": -1, "amount_cents": None},  # no overhead schedule in snapshots (O05)
        {"key": "quote_commissions", "label": "Quote commissions", "sign": -1,
         "amount_cents": sum_known((i.get("computed") or {}).get("pool_cents") for i in ready["items"]
                                   if i["kind"] == "quote_commission" and i["readiness"]["state"] != "not_meaningful")},
        {"key": "marketing_commissions", "label": "Marketing commissions", "sign": -1, "amount_cents": None},
    ])
    ratios = labor_revenue_ratios(stage1_total, None, revenue)

    jobs = []
    for j in snapshot.get("jobs", []):
        jobs.append({"job_id": j["id"], "display_name": j["display_name"], "status": j.get("status"),
                     "adjusted_invoice_cents": j.get("adjusted_invoice_cents"),
                     "final_payment_verified": j.get("final_payment_verified"),
                     "labor_cents_this_cycle": job_labor_cents(snapshot, j["id"]),
                     "included_costs_cents": sum(a["amount_cents"] for c in included_costs
                                                 for a in c.get("job_allocations", []) if a["job_id"] == j["id"]),
                     "open_exceptions": sum(1 for e in excs if e.get("state") != "resolved"
                                            and j["id"] in e["entity_refs"].get("job_ids", []))})

    totals = {
        "workers_in_cycle": len(earnings),
        "workers_review_ready": len(ready_gross),
        "stage1_gross_ready_cents": sum(ready_gross),
        "stage1_gross_all_cents": stage1_total,
        "minutes_in_cycle_known": sum(e["duration_minutes"] for e in entries_in if e.get("duration_minutes") is not None),
        "entries_in_cycle": len(entries_in),
        "entries_excluded_out_of_cycle": len(snapshot.get("time_entries", [])) - len(entries_in),
        "eligible_receipts_cents": revenue,
        "tips_cents": tips if not partial else None,
        "direct_expenses_included_cents": None if partial else sum_known(c.get("amount_cents") for c in included_costs),
        "open_exceptions": sum(1 for e in excs if e.get("state") != "resolved"),
        "cycle_profit_cents": bridge["result_cents"],
    }

    evidence = {"snapshot_id": snapshot.get("snapshot_id"), "captured_at": snapshot.get("captured_at"),
                "coverage": cyc.get("coverage", []),
                "time_entry_refs": [e.get("source_ref") for e in snapshot.get("time_entries", [])],
                "exception_evidence_count": sum(len(e.get("evidence", [])) for e in excs)}
    numeric = {"totals": totals, "earnings": [(e["worker_id"], e["gross_new_cents"], e["weekly_minutes"]) for e in earnings],
               "readiness": {i["id"]: (i["readiness"]["state"], sorted(b["code"] for b in i["readiness"]["blockers"]))
                             for i in ready["items"]},
               "stage1": ready["stage1"]["state"], "corrections": [c.get("id") for c in corrs],
               "exceptions": sorted((e["id"], e.get("state")) for e in excs), "calc": CALC_VERSION}
    draft_version = "draft_" + content_hash(numeric)[7:19]

    return {
        "packet_kind": "internal_review_packet", "contract_version": CONTRACT_VERSION,
        "calculation_version": CALC_VERSION, "draft_version": draft_version, "generated_at": now,
        "provenance": snapshot.get("provenance", "synthetic"), "partial_inputs": partial,
        "cycle": {k: cyc.get(k) for k in ("id", "company_label", "period_start", "period_end", "payday",
                                          "business_tz", "workweeks", "policy_version", "existing_run_status")},
        "destination": "internal_draft",
        "destination_note": "Internal review draft only. Not entered in Gusto; nothing submitted or paid.",
        "identities": [{"worker_id": w["id"], "display_name": w["display_name"],
                        "identity_status": w.get("identity_status"), "payment_route": w.get("payment_route")}
                       for w in snapshot.get("workers", [])],
        "earnings": earnings, "totals": totals,
        "readiness": {"stage1": ready["stage1"], "items": ready["items"], "stage2_summary": ready["stage2_summary"]},
        "profit_bridge": bridge, "labor_revenue": ratios, "jobs": jobs,
        "receipts": receipts, "costs": snapshot.get("costs", []), "obligations": snapshot.get("obligations", []),
        "time_entries": snapshot.get("time_entries", []), "exceptions": excs, "corrections": corrs,
        "evidence": evidence, "workbook_ref": None,
    }

