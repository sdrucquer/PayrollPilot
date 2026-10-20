import json
from pathlib import Path

import pytest

from payrollpilot_core.calc import (
    CalcBlocked,
    PolicyMissing,
    apply_settlement,
    cycle_profit_bridge,
    labor_revenue_ratios,
    manager_pool,
    quote_pool,
)

FIX = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "fixtures"
CASES = json.loads((FIX / "quote_pool_cases.json").read_text())["cases"]
SNAP = json.loads((FIX / "cycle_synthetic_v1.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_quote_pool_cases(case):
    args = (case["eligible_profit_cents"], case["quoters"], case["prior_paid"])
    kw = {"final_payment_verified": case["final_payment_verified"], "policy": SNAP["policies"]["quote_pool"]}
    if case["expect"]["ok"]:
        out = quote_pool(*args, **kw)
        assert out["pool_cents"] == case["expect"]["pool_cents"]
        assert out["shares"] == case["expect"]["shares"]
    else:
        with pytest.raises(CalcBlocked) as ei:
            quote_pool(*args, **kw)
        assert ei.value.code == case["expect"]["code"]


def test_t10_exact():
    out = quote_pool(100000, ["wkr_02", "wkr_03"], {})
    assert out["pool_cents"] == 5000 and out["shares"] == {"wkr_02": 2500, "wkr_03": 2500}


def test_policy_missing_codes_are_policy_missing():
    for profit, quoters in [(None, ["a"]), (0, ["a"]), (100000, ["a", "b", "c"])]:
        with pytest.raises(PolicyMissing):
            quote_pool(profit, quoters, {})


def test_unapproved_quote_policy_blocks():
    with pytest.raises(PolicyMissing) as ei:
        quote_pool(100000, ["a"], {}, policy={"status": "unresolved"})
    assert ei.value.code == "policy_missing:O03"


def test_t25_prior_paid_to_non_quoter_needs_decision():
    with pytest.raises(CalcBlocked) as ei:
        quote_pool(100000, ["wkr_03"], {"wkr_02": 2500})
    assert ei.value.code == "paid_recipient_changed"


def test_odd_cent_remainder_is_reported_not_hidden():
    out = quote_pool(100020, ["a", "b"], {})  # pool 5001
    assert out["pool_cents"] == 5001 and sum(out["gross_shares"].values()) + out["remainder_cents"] == 5001
    assert out["blockers"][0]["code"] == "policy_missing:O03_rounding"


def test_profit_bridge_each_component_once_and_null_propagates():
    comps = [{"key": "receipts", "sign": 1, "amount_cents": 450000},
             {"key": "direct_expenses", "sign": -1, "amount_cents": 120250},
             {"key": "gross_labor", "sign": -1, "amount_cents": 200000},
             {"key": "overhead", "sign": -1, "amount_cents": None}]
    out = cycle_profit_bridge(comps)
    assert out["result_cents"] is None
    assert [b["code"] for b in out["blockers"]] == ["component_unknown:overhead"]
    comps[3]["amount_cents"] = 10000
    assert cycle_profit_bridge(comps)["result_cents"] == 450000 - 120250 - 200000 - 10000
    with pytest.raises(ValueError):
        cycle_profit_bridge(comps + [{"key": "receipts", "sign": 1, "amount_cents": 1}])


def test_profit_bridge_optional_unknown_does_not_block():
    out = cycle_profit_bridge([{"key": "r", "sign": 1, "amount_cents": 100},
                               {"key": "adj", "sign": -1, "amount_cents": None, "required": False}])
    assert out["result_cents"] == 100


def test_t22_labor_revenue_ratios():
    r = labor_revenue_ratios(200000, 250000, 400000)
    assert r == {"base_ratio": 0.5, "total_ratio": 0.625, "not_meaningful": False, "threshold": None,
                 "review_status": "no_approved_threshold"}
    for denom in (0, -100, None):
        r = labor_revenue_ratios(200000, 250000, denom)
        assert r["not_meaningful"] and r["base_ratio"] is None and r["total_ratio"] is None
    assert labor_revenue_ratios(200000, None, 400000)["total_ratio"] is None  # missing employer cost stays unknown


APPROVED_SPLIT = {"status": "approved", "split_percent": {"retained": 50, "mgr_a": 10, "mgr_b": 20, "owner": 20},
                  "requires_resolution": []}


def test_manager_pool_uses_policy_split_only():
    out = manager_pool(100000, APPROVED_SPLIT)
    assert out["allocations"] == {"retained": 50000, "mgr_a": 10000, "mgr_b": 20000, "owner": 20000}


def test_manager_pool_refusals():
    with pytest.raises(PolicyMissing):
        manager_pool(100000, SNAP["policies"]["manager_split"])  # placeholder + requires_resolution
    with pytest.raises(PolicyMissing):
        manager_pool(100000, None)
    with pytest.raises(CalcBlocked) as ei:
        manager_pool(None, APPROVED_SPLIT)
    assert ei.value.code == "pool_unknown"
    for bad in (0, -5000):
        with pytest.raises(PolicyMissing):
            manager_pool(bad, APPROVED_SPLIT)
    with pytest.raises(PolicyMissing):
        manager_pool(100000, {**APPROVED_SPLIT, "split_percent": {"a": 60, "b": 30}})


def test_t26_role_change_does_not_move_named_split():
    workers_before = json.loads(json.dumps(SNAP["workers"]))
    alloc_before = manager_pool(100000, APPROVED_SPLIT)["allocations"]
    workers_before[1]["rates"][1]["category"] = "hourly"  # role change for a person
    workers_before[0]["rates"][0]["category"] = "team_leader"
    assert manager_pool(100000, APPROVED_SPLIT)["allocations"] == alloc_before


def test_t21_settlement_reduces_balance_no_new_earnings():
    obl = SNAP["obligations"][0]
    new = apply_settlement(obl, {"date": "2026-10-06", "amount_cents": 8900, "reference": "ach_1", "verified": True})
    assert new["balance_cents"] == 0 and new["status"] == "settled"
    assert new["gross_cents"] == obl["gross_cents"] == 8900
    assert obl["balance_cents"] == 8900 and obl["settlements"] == []  # input not mutated
    part = apply_settlement(obl, {"amount_cents": 4000})
    assert part["status"] == "settled_partial" and part["balance_cents"] == 4900


def test_t21_unknown_recognition_blocks():
    with pytest.raises(CalcBlocked) as ei:
        apply_settlement({**SNAP["obligations"][0], "recognition_cycle_id": None}, {"amount_cents": 100})
    assert ei.value.code == "prior_recognition_unknown"
    with pytest.raises(CalcBlocked):
        apply_settlement(SNAP["obligations"][0], {"amount_cents": 9000})
