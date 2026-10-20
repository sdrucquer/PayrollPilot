import copy
import json
from pathlib import Path

import pytest

from payrollpilot_core.audit import run_audit
from payrollpilot_core.corrections import CorrectionError, apply_corrections, propose_correction
from payrollpilot_core.readiness import cycle_readiness

FIX = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "fixtures"
MATRIX = json.loads((FIX / "readiness_matrix_v1.json").read_text())


@pytest.fixture()
def snap():
    return json.loads((FIX / "cycle_synthetic_v1.json").read_text())


T02_BEFORE = {"time_entry_id": "te_0014", "job_id": "job_01"}
T02_AFTER = {"time_entry_id": "te_0014", "job_id": "job_02"}


def test_t02_allocation_only_wages_zero_job_labor_moves(snap):
    corr = propose_correction("job_allocation", T02_BEFORE, T02_AFTER, snap)
    exp = MATRIX["after_t02_correction"]["correction"]["calculation_impact"]
    assert corr["calculation_impact"]["stage1_wages_delta_cents"] == 0 == exp["stage1_wages_delta_cents"]
    assert corr["calculation_impact"]["job_costing_delta"] == exp["job_costing_delta"]
    assert corr["state"] == "proposed" and corr["approval_id"] is None and corr["blockers"] == []
    assert corr["id"].startswith("corr_") and corr["target_version"].startswith("sha256:")


def test_t02_applied_view_matches_readiness_after(snap):
    corr = propose_correction("job_allocation", T02_BEFORE, T02_AFTER, snap)
    view = apply_corrections(snap, [corr])
    assert next(e for e in snap["time_entries"] if e["id"] == "te_0014")["job_id"] == "job_01"  # source untouched
    out = cycle_readiness(view, run_audit(view))
    for iid, exp in MATRIX["after_t02_correction"]["items"].items():
        got = out["items_by_id"][iid]["readiness"]
        assert {b["code"] for b in got["blockers"]} == {b["code"] for b in exp["blockers"]}, iid
    assert out["stage1"]["state"] == MATRIX["after_t02_correction"]["stage1"]["state"]


def test_deterministic_id(snap):
    a = propose_correction("job_allocation", T02_BEFORE, T02_AFTER, snap)
    b = propose_correction("job_allocation", T02_BEFORE, T02_AFTER, copy.deepcopy(snap))
    assert a == b


def test_stale_before_is_refused(snap):
    with pytest.raises(CorrectionError) as ei:
        propose_correction("job_allocation", {"time_entry_id": "te_0014", "job_id": "job_02"}, T02_AFTER, snap)
    assert ei.value.code == "stale_before"


def test_unknown_job_and_unsupported_identity_merge(snap):
    with pytest.raises(CorrectionError):
        propose_correction("job_allocation", T02_BEFORE, {"time_entry_id": "te_0014", "job_id": "job_99"}, snap)
    with pytest.raises(CorrectionError) as ei:
        propose_correction("identity_merge", {"worker_id": "wkr_04"}, {"worker_id": "wkr_04"}, snap)
    assert ei.value.code == "unsupported:identity_merge"


TIMER_AFTER = {"time_entry_id": "te_0021", "end": "2026-10-09T15:30:00-04:00", "duration_minutes": 480,
               "open_timer": False}


def _without_dup(snap):
    s = copy.deepcopy(snap)
    s["time_entries"] = [e for e in s["time_entries"] if e["id"] != "te_0018"]
    return s


def test_t20_prior_week_unknown_blocks_no_hours_times_rate(snap):
    corr = propose_correction("time_confirmation", {"time_entry_id": "te_0021", "duration_minutes": None},
                              TIMER_AFTER, _without_dup(snap))
    imp = corr["calculation_impact"]
    assert imp["stage1_wages_delta_cents"] is None  # NOT 480 min x 3000 = 24000
    assert "prior_recognition_unknown" in {b["code"] for b in corr["blockers"]}
    assert imp["workweek_reconciliation"]["minutes_after"] == 2400
    assert imp["workweek_reconciliation"]["gross_after_cents"] == 120000


def test_t20_reconciles_whole_week_against_prior_recognition(snap):
    s = _without_dup(snap)
    s["obligations"].append({"id": "obl_w", "kind": "wages", "worker_id": "wkr_02", "job_id": None,
                             "earning_period": {"start": "2026-10-05", "end": "2026-10-11"},
                             "recognition_cycle_id": "cyc_synth_v1", "gross_cents": 90000, "status": "recognized",
                             "settlements": [], "balance_cents": 90000})
    corr = propose_correction("time_confirmation", {"time_entry_id": "te_0021"}, TIMER_AFTER, s)
    assert corr["calculation_impact"]["stage1_wages_delta_cents"] == 120000 - 90000  # 30000, not 24000
    assert corr["blockers"] == []


def test_t20_overtime_week_flags_policy(snap):
    corr = propose_correction("time_confirmation", {"time_entry_id": "te_0021"}, TIMER_AFTER, snap)  # dup kept: 2880 min
    assert "policy_missing:O02_overtime" in {b["code"] for b in corr["blockers"]}


def test_rate_confirmation_first_computation(snap):
    after = {"worker_id": "wkr_03", "payment_route": "manual",
             "rates": [{"effective_from": "2026-09-01", "effective_to": None, "rate_cents_per_hour": 2500,
                        "category": "hourly", "evidence": None, "status": "verified"}]}
    corr = propose_correction("rate_confirmation", {"worker_id": "wkr_03", "payment_route": "unknown"}, after, snap)
    imp = corr["calculation_impact"]
    assert imp["worker_gross"] == {"worker_id": "wkr_03", "before_cents": None, "after_cents": 88083}
    assert imp["stage1_wages_delta_cents"] is None
    assert "first_computation" in {b["code"] for b in corr["blockers"]}


def test_rate_change_on_paid_entry_needs_adjustment_decision(snap):
    rates = copy.deepcopy(snap["workers"][1]["rates"])
    rates[0]["rate_cents_per_hour"] = 2600
    corr = propose_correction("rate_confirmation", {"worker_id": "wkr_02"}, {"worker_id": "wkr_02", "rates": rates}, snap)
    assert "paid_adjustment_decision" in {b["code"] for b in corr["blockers"]}


def test_cost_link_must_reconcile_to_total(snap):
    corr = propose_correction("cost_link", {"cost_id": "cost_04"},
                              {"cost_id": "cost_04", "job_allocations": [{"job_id": "job_01", "amount_cents": 12575}],
                               "allocated": True, "categorized": True}, snap)
    assert corr["calculation_impact"]["job_costing_delta"] == [{"job_id": "job_01", "cost_delta_cents": 12575}]
    assert corr["calculation_impact"]["stage1_wages_delta_cents"] == 0
    with pytest.raises(CorrectionError) as ei:
        propose_correction("cost_link", {"cost_id": "cost_04"},
                           {"cost_id": "cost_04", "job_allocations": [{"job_id": "job_01", "amount_cents": 10000}]}, snap)
    assert ei.value.code == "allocation_mismatch"
    with pytest.raises(CorrectionError):
        propose_correction("cost_link", {"cost_id": "cost_05"},
                           {"cost_id": "cost_05", "job_allocations": [{"job_id": "job_01", "amount_cents": 8900}]}, snap)
