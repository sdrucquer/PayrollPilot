"""Compensation and reconciliation calculations. Pure, Decimal, integer cents, round half-even once.

Never invents a rate, percentage, overhead, threshold or tax treatment. Missing or open policy raises
PolicyMissing (a normal, expected outcome rendered as a blocker). Unknown inputs produce None results.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable

from .money import percent_of, to_cents

# The quote-pool rule is an approved SOP rule (PRD 6.2, decision O03): one pool = 5% of eligible
# full-job profit after final payment; two confirmed quoters split it equally. Callers should pass the
# policy from the snapshot / private policy file; this mirror is used only when none is passed.
SOP_QUOTE_POOL_POLICY = {"decision_id": "O03", "status": "approved", "pool_percent": 5, "max_quoters": 2,
                         "requires_final_payment": True}


class CalcBlocked(Exception):
    """A calculation cannot produce an authoritative number. `code` is a readiness blocker code."""

    def __init__(self, code: str, label: str):
        super().__init__(f"{code}: {label}")
        self.code = code
        self.label = label

    def as_blocker(self, exception_id: str | None = None) -> dict:
        return {"code": self.code, "label": self.label, "exception_id": exception_id}


class PolicyMissing(CalcBlocked):
    """Required business policy is missing, open, or does not cover this case."""


# ------------------------------------------------------------------ quote commission
def quote_pool(eligible_profit_cents: int | None, quoters: list[str], prior_paid: dict[str, int] | None = None,
               *, final_payment_verified: bool = True, policy: dict | None = None) -> dict:
    """Single pool = profit x pool_percent; split equally among confirmed quoters; minus prior paid per person.

    Returns {"pool_cents", "shares": {worker_id: cents}, "gross_shares", "prior_paid", "remainder_cents",
    "blockers": []}. Raises PolicyMissing / CalcBlocked instead of guessing.
    """
    pol = policy or SOP_QUOTE_POOL_POLICY
    prior_paid = dict(prior_paid or {})
    if pol.get("status") != "approved" or pol.get("pool_percent") is None:
        raise PolicyMissing("policy_missing:O03", "Quote pool policy not approved")
    if pol.get("requires_final_payment", True) and not final_payment_verified:
        raise PolicyMissing("policy_missing:final_payment", "Final payment not verified (SOP rule)")
    if eligible_profit_cents is None:
        raise PolicyMissing("policy_missing:profit_unknown", "Eligible full-job profit unknown")
    if eligible_profit_cents <= 0:
        raise PolicyMissing("policy_missing:O03_nonpositive_profit",
                            "Zero/negative job profit: commission behavior is an open owner decision (O03)")
    if not quoters:
        raise CalcBlocked("attribution_unconfirmed", "No confirmed quoter")
    if len(set(quoters)) != len(quoters):
        raise CalcBlocked("attribution_unconfirmed", "Duplicate quoter ids")
    if len(quoters) > int(pol.get("max_quoters", 2)):
        raise PolicyMissing("policy_missing:O03_more_than_two_quoters",
                            "More than two quoters: sharing rule is an open owner decision (O03)")
    strays = sorted(set(prior_paid) - set(quoters))
    if strays:
        raise CalcBlocked("paid_recipient_changed",
                          f"Prior commission paid to non-quoter(s) {strays}: adjustment decision required (T25)")

    pool_exact = percent_of(eligible_profit_cents, pol["pool_percent"])
    pool_cents = to_cents(pool_exact)
    n = len(quoters)
    gross = {q: to_cents(Decimal(pool_cents) / n) for q in quoters}
    remainder = pool_cents - sum(gross.values())
    shares = {}
    for q in quoters:
        net = gross[q] - prior_paid.get(q, 0)
        if net < 0:
            raise CalcBlocked("prior_paid_exceeds_share",
                              f"Prior paid to {q} exceeds the computed share: adjustment decision required")
        shares[q] = net
    blockers = []
    if remainder:
        blockers.append({"code": "policy_missing:O03_rounding",
                         "label": f"{remainder} cent remainder after equal split; rounding policy open",
                         "exception_id": None})
    return {"pool_cents": pool_cents, "shares": shares, "gross_shares": gross, "prior_paid": prior_paid,
            "remainder_cents": remainder, "blockers": blockers}


# ------------------------------------------------------------------ cycle profit bridge
def cycle_profit_bridge(components: Iterable[dict]) -> dict:
    """Receipts-to-profit bridge. Each component: {"key", "label", "sign": +1|-1, "amount_cents": int|None,
    "required": bool (default True), "evidence": [...], "status": str}. Each key may appear once.
    Result is None (with blockers) when any required component is unknown."""
    lines, seen, blockers = [], set(), []
    total = 0
    for c in components:
        key = c["key"]
        if key in seen:
            raise ValueError(f"component {key!r} appears twice; each component is counted once")
        seen.add(key)
        sign = c.get("sign", -1)
        if sign not in (1, -1):
            raise ValueError("sign must be +1 or -1")
        amt = c.get("amount_cents")
        required = c.get("required", True)
        lines.append({"key": key, "label": c.get("label", key), "sign": sign, "amount_cents": amt,
                      "required": required, "evidence": c.get("evidence", []), "status": c.get("status")})
        if amt is None:
            if required:
                blockers.append({"code": f"component_unknown:{key}", "label": f"{c.get('label', key)} unknown",
                                 "exception_id": None})
            continue
        total += sign * amt
    return {"lines": lines, "result_cents": None if blockers else total, "blockers": blockers,
            "note": "before manager distributions and their unresolved employer-cost treatment"}


# ------------------------------------------------------------------ labor / revenue review
def labor_revenue_ratios(base_wages_cents: int | None, total_labor_cents: int | None,
                         eligible_revenue_cents: int | None) -> dict:
    """Separate base and total labor ratios to eligible collected revenue. No threshold, no judgment.
    Zero/negative/unknown denominator -> not meaningful (never infinite)."""
    if eligible_revenue_cents is None or eligible_revenue_cents <= 0:
        return {"base_ratio": None, "total_ratio": None, "not_meaningful": True, "threshold": None,
                "review_status": "not_meaningful"}

    def ratio(x):
        return None if x is None else float((Decimal(x) / Decimal(eligible_revenue_cents)).quantize(Decimal("0.0001")))

    return {"base_ratio": ratio(base_wages_cents), "total_ratio": ratio(total_labor_cents), "not_meaningful": False,
            "threshold": None, "review_status": "no_approved_threshold"}


# ------------------------------------------------------------------ manager pool
def manager_pool(pool_cents: int | None, policy: dict | None) -> dict:
    """Split an approved positive pool by the policy's named recipients. Percentages come ONLY from the
    passed-in policy (private file at runtime; placeholders in fixtures). Refuses rather than guesses."""
    if not policy or not policy.get("split_percent"):
        raise PolicyMissing("policy_missing:O06", "Manager allocation policy not supplied")
    if policy.get("status") != "approved":
        raise PolicyMissing("policy_missing:O06", f"Manager allocation status is {policy.get('status')!r}, not approved")
    if policy.get("requires_resolution"):
        raise PolicyMissing("policy_missing:O06", "Unresolved: " + ", ".join(policy["requires_resolution"]))
    if pool_cents is None:
        raise CalcBlocked("pool_unknown", "Cycle pool unknown")
    if pool_cents <= 0:
        raise PolicyMissing("policy_missing:O05_nonpositive_pool",
                            "Zero/negative pool: no distributions, no invented loss carry-forward")
    split = {k: Decimal(str(v)) for k, v in policy["split_percent"].items()}
    if sum(split.values()) != 100:
        raise PolicyMissing("policy_missing:O06", "Split percentages do not sum to 100")
    alloc = {k: to_cents(Decimal(pool_cents) * pct / 100) for k, pct in split.items()}
    remainder = pool_cents - sum(alloc.values())
    blockers = []
    if remainder:
        blockers.append({"code": "policy_missing:O06_rounding", "label": f"{remainder} cent rounding remainder",
                         "exception_id": None})
    return {"pool_cents": pool_cents, "allocations": alloc, "remainder_cents": remainder, "blockers": blockers}


# ------------------------------------------------------------------ obligations vs settlement (T21)
def apply_settlement(obligation: dict, settlement: dict) -> dict:
    """Return a NEW obligation with the settlement appended and balance reduced. Never creates earnings
    (gross unchanged) or a second cost recognition. Unknown recognition/balance -> CalcBlocked."""
    amt = settlement.get("amount_cents")
    if amt is None or amt <= 0:
        raise CalcBlocked("settlement_amount_unknown", "Settlement amount missing or non-positive")
    if obligation.get("recognition_cycle_id") is None or obligation.get("balance_cents") is None:
        raise CalcBlocked("prior_recognition_unknown",
                          "Earlier recognition unknown: open a reconciliation issue, do not deduct again")
    if amt > obligation["balance_cents"]:
        raise CalcBlocked("settlement_exceeds_balance", "Settlement exceeds outstanding balance")
    new = dict(obligation)
    new["settlements"] = list(obligation.get("settlements", [])) + [dict(settlement)]
    new["balance_cents"] = obligation["balance_cents"] - amt
    new["status"] = "settled" if new["balance_cents"] == 0 else "settled_partial"
    new["gross_cents"] = obligation.get("gross_cents")
    return new


def try_calc(fn, *args, **kwargs) -> tuple[Any, list[dict]]:
    """(result, []) or (None, [blocker]) — convenience for readiness/packet code."""
    try:
        return fn(*args, **kwargs), []
    except CalcBlocked as e:
        return None, [e.as_blocker()]
