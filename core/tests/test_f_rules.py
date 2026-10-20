"""F-02 core rules (lane F): property-style checks over mutated synthetic snapshots. No IO.

- readiness is never "ready" when a required money/time input is null (T11, T22)
- manager-pool policy state never changes commission, tip or wage readiness (T24, T09)
- allocation-only correction never changes wages (T02)
- no default policy: removing a policy never turns an item green (T11)
"""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from payrollpilot_core.audit import run_audit
from payrollpilot_core.corrections import apply_corrections, propose_correction
from payrollpilot_core.readiness import cycle_readiness, worker_gross_cents

SNAP = json.loads((Path(__file__).resolve().parents[2] / "docs" / "contracts" / "fixtures"
                   / "cycle_synthetic_v1.json").read_text())


def cards(out):
    yield "stage1", out["stage1"]
    yield from out["workers"].items()
    for i in out["items"]:
        yield i["id"], i["readiness"]


def clean_snapshot():
    """Policy-complete synthetic variant where Worker A and Job 01's commission are ready."""
    s = copy.deepcopy(SNAP)
    s["jobs"][0]["quoter_candidates"] = [{"worker_id": "wkr_01", "basis": "confirmed_by_owner"}]
    s["time_entries"] = [e for e in s["time_entries"] if e["worker_id"] == "wkr_01" and e["id"] != "te_0033"]
    s["costs"] = [c for c in s["costs"] if c["id"] in ("cost_02", "cost_03")]
    s["jobs"] = s["jobs"][:2]
    s["receipts"] = [r for r in s["receipts"] if r["id"] != "rcpt_02"]
    for c in s["cycle"]["coverage"]:
        c["complete"] = True
    return s


def test_clean_variant_has_ready_cards():
    out = cycle_readiness(clean_snapshot(), run_audit(clean_snapshot()))
    assert out["workers"]["wkr_01"]["state"] == "ready"
    assert out["items_by_id"]["ci_quote_job_01"]["readiness"]["state"] == "ready"


@pytest.mark.parametrize("seed", range(25))
def test_never_ready_with_null_input(seed):
    rng = random.Random(seed)
    s = clean_snapshot()
    target = rng.choice(["duration", "rate", "invoice"])
    if target == "duration":
        e = rng.choice(s["time_entries"])
        e["duration_minutes"] = None
        affected = {"wkr_01", "stage1"} | ({"ci_quote_job_01"} if e["job_id"] == "job_01" else set())
    elif target == "rate":
        s["workers"][0]["rates"][0]["rate_cents_per_hour"] = None
        affected = {"wkr_01", "stage1", "ci_quote_job_01"}
    else:
        s["jobs"][0]["adjusted_invoice_cents"] = None
        affected = {"ci_quote_job_01"}
    out = cycle_readiness(s, run_audit(s))
    for key, r in cards(out):
        if r["state"] == "ready":
            assert not r["unknown_amount"], (seed, key)
        if key in affected:
            assert r["state"] != "ready", (seed, target, key, r)


def _manager_variants():
    approved = {"decision_id": "O06", "status": "approved", "requires_resolution": [],
                "split_percent": {"retained": 40, "mgr_a": 15, "mgr_b": 25, "owner": 20}}
    return [None, {"manager_split": approved}, {"manager_split": approved, "overhead_allocation": {"status": "approved"}},
            {"manager_split": {"status": "unresolved"}, "overhead_allocation": {"status": "unresolved"}}]


@pytest.mark.parametrize("base", ["synthetic", "clean"])
def test_manager_pool_policy_never_moves_other_cards(base):
    s = copy.deepcopy(SNAP) if base == "synthetic" else clean_snapshot()
    excs = run_audit(s)
    seen = []
    for pol in _manager_variants():
        out = cycle_readiness(s, excs, policies=pol)
        seen.append({k: r for k, r in cards(out) if k != "ci_manager_pool"})
    assert all(v == seen[0] for v in seen[1:])


def test_negative_cycle_pool_does_not_cancel_commission():
    s = clean_snapshot()
    s["costs"].append({"id": "cost_99", "amount_cents": 10_000_000, "description": "large synthetic cycle cost",
                       "cost_date": "2026-10-09", "representations": [{"kind": "receipt", "source_ref": {"system": "fixture",
                       "record_id": "r99", "url": None, "captured_at": None, "snapshot_id": None}, "amount_cents": 10_000_000}],
                       "job_allocations": [{"job_id": "job_02", "amount_cents": 10_000_000}], "categorized": True,
                       "allocated": True, "included_in_calc": True, "supersedes_cost_id": None, "conflict": None,
                       "provenance": "synthetic"})
    out = cycle_readiness(s, run_audit(s))
    assert out["items_by_id"]["ci_quote_job_01"]["readiness"]["state"] == "ready"
    assert out["items_by_id"]["ci_manager_pool"]["readiness"]["state"] == "blocked"


@pytest.mark.parametrize("te_id,new_job", [("te_0014", "job_02"), ("te_0001", "job_02"), ("te_0026", "job_01"),
                                           ("te_0005", "job_01")])
def test_allocation_only_correction_never_changes_wages(te_id, new_job):
    s = copy.deepcopy(SNAP)
    te = next(e for e in s["time_entries"] if e["id"] == te_id)
    corr = propose_correction("job_allocation", {"time_entry_id": te_id, "job_id": te["job_id"]},
                              {"time_entry_id": te_id, "job_id": new_job}, s)
    assert corr["calculation_impact"]["stage1_wages_delta_cents"] in (0, None)
    view = apply_corrections(s, [corr])
    for w in {e["worker_id"] for e in s["time_entries"]}:
        assert worker_gross_cents(view, w) == worker_gross_cents(s, w)
    before, after = cycle_readiness(s, run_audit(s)), cycle_readiness(view, run_audit(view))
    assert before["workers"] == after["workers"]


@pytest.mark.parametrize("policy_key", ["quote_pool", "tip_rule", "overhead_allocation", "marketing", "manager_split"])
def test_removing_a_policy_never_turns_an_item_green(policy_key):
    s = clean_snapshot()
    base = {k: r["state"] for k, r in cards(cycle_readiness(s, run_audit(s)))}
    s2 = copy.deepcopy(s)
    s2["policies"].pop(policy_key, None)
    after = {k: r["state"] for k, r in cards(cycle_readiness(s2, run_audit(s2)))}
    for k, st in after.items():
        if st == "ready":
            assert base[k] == "ready", (policy_key, k)
