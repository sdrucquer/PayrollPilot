import copy
import json
from pathlib import Path

import pytest

from payrollpilot_core.audit import audit_key, run_audit

FIX = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "fixtures"
CATEGORIES = {"missing_job", "long_shift", "open_timer", "overlap", "duplicate_time", "unassigned_time",
              "schedule_mismatch", "identity", "rate_unconfirmed", "already_paid_allocation", "unmatched_cost",
              "cost_conflict", "offsite_link", "quote_attribution", "policy_missing", "coverage_gap"}


@pytest.fixture()
def snap():
    return json.loads((FIX / "cycle_synthetic_v1.json").read_text())


@pytest.fixture()
def expected():
    return json.loads((FIX / "expected_exceptions_v1.json").read_text())


def test_matches_expected_exceptions_setwise(snap, expected):
    got = run_audit(snap)
    assert {audit_key(e) for e in got} == {audit_key(e) for e in expected["exceptions"]}
    assert len(got) == expected["expected_count"]


def test_ids_stage_impact_and_respondent_match_expected(snap, expected):
    got = {e["id"]: e for e in run_audit(snap)}
    for exp in expected["exceptions"]:
        g = got[exp["id"]]
        assert g["category"] == exp["category"]
        assert g["stage_impact"] == exp["stage_impact"], exp["category"]
        assert g["intended_respondent_role"] == exp["intended_respondent_role"], exp["category"]


def test_deterministic_ids_across_runs(snap):
    assert run_audit(copy.deepcopy(snap)) == run_audit(copy.deepcopy(snap))


def test_contract_shape(snap):
    for e in run_audit(snap):
        assert e["category"] in CATEGORIES
        assert e["id"].startswith("exc_") and e["cycle_id"] == "cyc_synth_v1"
        assert e["state"] == "detected" and e["owner_agent"] == "audit"
        assert e["evidence"], f"{e['category']} has no evidence"
        assert e["provenance"] in ("real", "seeded_issue", "synthetic")
        assert e["intended_respondent_role"] in ("ops_lead", "owner", "worker", "quoter", "accountant")
        assert set(e["entity_refs"]) >= {"worker_id", "time_entry_ids", "job_ids", "cost_ids"}
        assert e["message_ids"] == [] and e["resolution_id"] is None


def test_t01_missing_job_unknown_rate_dollars_null(snap):
    exc = next(e for e in run_audit(snap) if e["category"] == "missing_job")
    assert exc["dollars_affected_cents"] is None  # rate unconfirmed: never 0, never invented
    assert "134 min" in exc["observed"]


def test_t02_already_paid_allocation_does_not_touch_wages(snap):
    exc = next(e for e in run_audit(snap) if e["category"] == "already_paid_allocation")
    assert exc["stage_impact"] == {"stage1_wages": "none", "stage2_costs": "job_costing"}
    assert exc["entity_refs"]["time_entry_ids"] == ["te_0014"]
    assert exc["dollars_affected_cents"] == 20000  # 480 min at the verified 2500 rate: job costing exposure


def test_t03_long_shift_is_flagged_never_trimmed(snap):
    before = copy.deepcopy(snap["time_entries"])
    exc = next(e for e in run_audit(snap) if e["category"] == "long_shift")
    assert exc["entity_refs"]["time_entry_ids"] == ["te_0029"]
    assert snap["time_entries"] == before  # input untouched; no hours trimmed or breaks added


def test_t07_shared_cost_reconciles_no_exception(snap):
    cats = {(e["category"], tuple(e["entity_refs"]["cost_ids"])) for e in run_audit(snap)}
    assert ("unmatched_cost", ("cost_03",)) not in cats and ("cost_conflict", ("cost_03",)) not in cats


def test_t07_shared_cost_allocation_mismatch_is_conflict(snap):
    snap["costs"][2]["job_allocations"][1]["amount_cents"] = 30000  # 25000 + 30000 != 60000
    cats = {(e["category"], tuple(e["entity_refs"]["cost_ids"])) for e in run_audit(snap)}
    assert ("cost_conflict", ("cost_03",)) in cats


def test_t23_bank_plus_jobber_same_cost_is_not_a_duplicate_expense(snap):
    # cost_02 has two representations with equal amounts: one identity, no exception
    assert not [e for e in run_audit(snap) if "cost_02" in e["entity_refs"]["cost_ids"]]


def test_t13_incomplete_coverage_produces_gap(snap):
    gaps = [e for e in run_audit(snap) if e["category"] == "coverage_gap"]
    assert [g["entity_refs"]["coverage"] for g in gaps] == [["quickbooks:expenses"]]
    snap["cycle"]["coverage"][0]["complete"] = False
    snap["cycle"]["coverage"][0]["incomplete_reason"] = "pagination_cut"
    gaps = [e for e in run_audit(snap) if e["category"] == "coverage_gap"]
    assert len(gaps) == 2
    tg = next(g for g in gaps if g["entity_refs"]["coverage"] == ["jobber:time_entries"])
    assert tg["stage_impact"]["stage1_wages"] == "blocks_item"


def test_t27_out_of_cycle_entry_excluded_and_reported(snap):
    excs = run_audit(snap)
    trap = [e for e in excs if "te_0033" in e["entity_refs"]["time_entry_ids"]]
    assert len(trap) == 1 and trap[0]["category"] == "unassigned_time"
    assert trap[0]["stage_impact"]["stage1_wages"] == "none"
    assert "prior payment unknown" in trap[0]["title"]


def test_entry_after_period_end_also_excluded(snap):
    e = copy.deepcopy(snap["time_entries"][0])
    e.update(id="te_9999", date="2026-10-12", start="2026-10-12T07:00:00-04:00", end="2026-10-12T19:00:00-04:00",
             duration_minutes=720)
    snap["time_entries"].append(e)
    hits = [x for x in run_audit(snap) if "te_9999" in x["entity_refs"]["time_entry_ids"]]
    assert [h["category"] for h in hits] == ["unassigned_time"]  # no long_shift: not in this cycle


def test_rate_change_mid_cycle_both_verified_no_exception(snap):
    assert not [e for e in run_audit(snap) if e["category"] == "rate_unconfirmed" and e["entity_refs"]["worker_id"] == "wkr_02"]


def test_rate_gap_mid_cycle_flags(snap):
    snap["workers"][1]["rates"][1]["status"] = "unconfirmed"
    hits = [e for e in run_audit(snap) if e["category"] == "rate_unconfirmed"]
    assert {h["entity_refs"]["worker_id"] for h in hits} == {"wkr_02", "wkr_03"}


def test_clean_snapshot_has_no_exceptions():
    snap = json.loads((FIX / "cycle_synthetic_v1.json").read_text())
    snap["time_entries"] = [e for e in snap["time_entries"] if e["worker_id"] == "wkr_01" and e["id"] != "te_0033"]
    snap["costs"] = [c for c in snap["costs"] if c["id"] in ("cost_02", "cost_03")]
    snap["jobs"][0]["quoter_candidates"] = [{"worker_id": "wkr_02", "basis": "confirmed_by_owner"}]
    snap["jobs"] = snap["jobs"][:2]
    for c in snap["cycle"]["coverage"]:
        c["complete"] = True
    assert run_audit(snap) == []
