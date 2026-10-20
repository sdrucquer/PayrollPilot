import copy
import json
from pathlib import Path

import pytest

from payrollpilot_core.audit import run_audit
from payrollpilot_core.readiness import (
    cycle_readiness,
    eligible_receipts_cents,
    job_labor_cents,
    readiness_for,
    worker_gross_cents,
)

FIX = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "fixtures"
MATRIX = json.loads((FIX / "readiness_matrix_v1.json").read_text())


@pytest.fixture()
def snap():
    return json.loads((FIX / "cycle_synthetic_v1.json").read_text())


def codes(r):
    return {(b["code"], b["exception_id"]) for b in r["blockers"]}


def assert_matches(got, exp, label):
    assert got["state"] == exp["state"], label
    assert got["unknown_amount"] == exp["unknown_amount"], label
    assert codes(got) == codes(exp), label
    assert got["calculation_version"] == "calc_v1"


def apply_t02(snapshot):
    s = copy.deepcopy(snapshot)
    te = next(e for e in s["time_entries"] if e["id"] == "te_0014")
    te["job_id"] = "job_02"
    return s


@pytest.mark.parametrize("phase", ["before", "after_t02_correction"])
def test_readiness_matrix(snap, phase):
    s = snap if phase == "before" else apply_t02(snap)
    out = cycle_readiness(s, run_audit(s))
    exp = MATRIX[phase]
    assert_matches(out["stage1"], exp["stage1"], "stage1")
    assert set(out["workers"]) == set(exp["workers"])
    for wid, r in exp["workers"].items():
        assert_matches(out["workers"][wid], r, wid)
    assert set(out["items_by_id"]) == set(exp["items"])
    for iid, r in exp["items"].items():
        assert_matches(out["items_by_id"][iid]["readiness"], r, iid)
    for wid, cents in exp["stage1_gross_new_cents"].items():
        assert worker_gross_cents(s, wid) == cents, wid


def test_t02_correction_leaves_wages_unchanged(snap):
    before = cycle_readiness(snap, run_audit(snap))
    s = apply_t02(snap)
    after = cycle_readiness(s, run_audit(s))
    assert before["stage1"] == after["stage1"] and before["workers"] == after["workers"]
    assert {w: worker_gross_cents(snap, w) for w in before["workers"]} == {w: worker_gross_cents(s, w) for w in after["workers"]}


def test_t24_manager_blockers_never_on_commission_cards(snap):
    out = cycle_readiness(snap, run_audit(snap))
    mgr_only = {"policy_missing:O05", "policy_missing:O06", "stage1_exposure", "commissions_pending"}
    for item in out["items"]:
        if item["kind"] != "manager_pool":
            assert not mgr_only & {b["code"] for b in item["readiness"]["blockers"]}, item["id"]


def test_t09_cost_blockers_never_invalidate_wages(snap):
    out = cycle_readiness(snap, run_audit(snap))
    stage2_exc = {b["exception_id"] for i in out["items"] for b in i["readiness"]["blockers"] if b["exception_id"]}
    assert out["workers"]["wkr_01"]["state"] == "ready"
    # Worker A's job (job_01/02) has cost and commission blockers; none reach the wage card
    assert not out["workers"]["wkr_01"]["blockers"]
    assert stage2_exc  # sanity: there are stage-2 blockers


def test_t24_commission_ready_while_manager_pool_blocked(snap):
    # Policy-complete synthetic job: confirmed quoter, known labor, no touching exceptions
    s = copy.deepcopy(snap)
    s["jobs"][0]["quoter_candidates"] = [{"worker_id": "wkr_02", "basis": "confirmed_by_owner"},
                                         {"worker_id": "wkr_01", "basis": "confirmed_by_ops"}]
    s["time_entries"] = [e for e in s["time_entries"] if e["worker_id"] in ("wkr_01",) and e["id"] != "te_0033"]
    s["costs"] = [c for c in s["costs"] if c["id"] in ("cost_02", "cost_03")]
    s["jobs"] = s["jobs"][:2]
    s["receipts"] = [r for r in s["receipts"] if r["id"] != "rcpt_02"]  # no pre-cycle history
    s["cycle"]["coverage"] = [c for c in s["cycle"]["coverage"] if c["complete"]]
    out = cycle_readiness(s, run_audit(s))
    q = out["items_by_id"]["ci_quote_job_01"]
    assert q["readiness"]["state"] == "ready", q["readiness"]["blockers"]
    labor = job_labor_cents(s, "job_01")
    profit = 480000 - labor - 42000 - 25000
    assert q["inputs"]["eligible_profit_cents"] == profit
    assert q["computed"]["pool_cents"] == round(profit * 5 / 100)
    assert out["items_by_id"]["ci_manager_pool"]["readiness"]["state"] == "blocked"


def test_t12_tip_excluded_from_receipts_and_pending(snap):
    assert eligible_receipts_cents(snap) == 300000 + 150000  # tip rcpt_04 and prior-cycle deposit excluded
    out = cycle_readiness(snap, run_audit(snap))
    assert out["items_by_id"]["ci_tip_rcpt_04"]["readiness"]["state"] == "pending"


def test_t19_proposed_allocation_does_not_exclude_revenue(snap):
    assert eligible_receipts_cents(snap) == 450000  # rcpt_01 proposed to prior cycle: still counted here
    s = copy.deepcopy(snap)
    s["receipts"][0]["cycle_allocation"]["state"] = "approved"
    assert eligible_receipts_cents(s) == 450000  # approval alone is insufficient
    s["receipts"][0]["cycle_allocation"].update(state="finalized", finalization_evidence={"system": "fixture", "record_id": "fin_1"})
    assert eligible_receipts_cents(s) == 150000


def test_t11_no_default_policy_turns_items_green(snap):
    out = cycle_readiness(snap, run_audit(snap))
    mk = out["items_by_id"]["ci_marketing_job_01"]["readiness"]
    assert mk["state"] == "pending" and {b["code"] for b in mk["blockers"]} == {"policy_missing:O04"}
    assert "policy_missing:O05" in {b["code"] for b in out["items_by_id"]["ci_manager_pool"]["readiness"]["blockers"]}


def test_private_policy_override_is_respected(snap):
    out = cycle_readiness(snap, run_audit(snap), policies={"tip_rule": {"status": "approved"}})
    codes_ = {b["code"] for b in out["items_by_id"]["ci_tip_rcpt_04"]["readiness"]["blockers"]}
    assert "policy_missing:O07" not in codes_ and "prior_payment_unknown" in codes_


def test_readiness_for_single_item_matches_cycle(snap):
    excs = run_audit(snap)
    out = cycle_readiness(snap, excs)
    for item in out["items"]:
        assert readiness_for(item, excs, snapshot=snap) == item["readiness"]


def test_resolved_exception_no_longer_blocks(snap):
    excs = run_audit(snap)
    for e in excs:
        if e["entity_refs"]["worker_id"] == "wkr_02" and e["stage_impact"]["stage1_wages"] != "none":
            e["state"] = "resolved"
    out = cycle_readiness(snap, excs)
    # case state says resolved, but the open timer's minutes are still null: never falsely ready
    assert out["workers"]["wkr_02"]["state"] == "blocked"
    assert [b["code"] for b in out["workers"]["wkr_02"]["blockers"]] == ["amount_unknown:wages"]
    s = copy.deepcopy(snap)
    te = next(e for e in s["time_entries"] if e["id"] == "te_0021")
    te.update(end="2026-10-09T15:30:00-04:00", duration_minutes=480, open_timer=False)
    excs2 = [e for e in run_audit(s) if e["category"] != "duplicate_time"]  # duplicate confirmed + removed
    s["time_entries"] = [e for e in s["time_entries"] if e["id"] != "te_0018"]
    assert cycle_readiness(s, run_audit(s))["workers"]["wkr_02"]["state"] == "ready"
    assert excs2


def test_stage1_readiness_snapshot_form_and_legacy_list_form(snap):
    from payrollpilot_core.readiness import stage1_readiness
    excs = run_audit(snap)
    r = stage1_readiness(snap, excs)
    assert r == cycle_readiness(snap, excs)["stage1"] and r["state"] == "partial"
    legacy = stage1_readiness(snap["workers"], excs)  # no time data: never ready, amounts unknown
    assert legacy["state"] == "blocked" and legacy["unknown_amount"] is True
