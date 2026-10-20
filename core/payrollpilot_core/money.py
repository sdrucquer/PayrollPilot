"""Money helpers. Integer cents everywhere; Decimal for arithmetic; round half-even ONCE at the end.

Unknown money is None and propagates as None. It is never coerced to 0.
"""
from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Iterable


class MoneyError(ValueError):
    pass


def to_cents(value: Decimal) -> int:
    """Final rounding step: Decimal cents -> int cents, half-even."""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def cents(amount: str | int | Decimal | None) -> int | None:
    """Parse a dollar amount ("12.34", "$1,000", Decimal) into integer cents. None stays None.

    Ints are treated as dollars only when passed as str; an int argument is assumed to already be cents.
    """
    if amount is None:
        return None
    if isinstance(amount, bool):
        raise MoneyError("bool is not money")
    if isinstance(amount, int):
        return amount
    if isinstance(amount, float):
        raise MoneyError("floats are not accepted for money; pass str or Decimal")
    text = str(amount).strip().replace(",", "").replace("$", "")
    try:
        dollars = Decimal(text)
    except InvalidOperation as e:
        raise MoneyError(f"invalid amount: {amount!r}") from e
    return to_cents(dollars * 100)


def gross_wages(minutes: int | None, rate_cents_per_hour: int | None) -> int | None:
    """minutes x rate / 60, Decimal, rounded half-even once. Any unknown input -> None."""
    if minutes is None or rate_cents_per_hour is None:
        return None
    if minutes < 0 or rate_cents_per_hour < 0:
        raise MoneyError("negative minutes or rate")
    return to_cents(Decimal(minutes) * Decimal(rate_cents_per_hour) / Decimal(60))


def gross_wages_exact(minutes: int | None, rate_cents_per_hour: int | None) -> Decimal | None:
    """Unrounded Decimal cents, for summing several segments before the single final rounding."""
    if minutes is None or rate_cents_per_hour is None:
        return None
    if minutes < 0 or rate_cents_per_hour < 0:
        raise MoneyError("negative minutes or rate")
    return Decimal(minutes) * Decimal(rate_cents_per_hour) / Decimal(60)


def sum_known(values: Iterable[int | None]) -> int | None:
    """Sum of cents; if ANY value is None the total is unknown (None)."""
    total = 0
    for v in values:
        if v is None:
            return None
        total += v
    return total


def percent_of(amount_cents: int, percent: int | str | Decimal) -> Decimal:
    """Unrounded Decimal cents for amount x percent / 100."""
    return Decimal(amount_cents) * Decimal(str(percent)) / Decimal(100)
