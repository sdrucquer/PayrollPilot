from decimal import Decimal

import pytest

from payrollpilot_core.money import MoneyError, cents, gross_wages, gross_wages_exact, sum_known, to_cents


def test_cents_parsing():
    assert cents("12.34") == 1234
    assert cents("$1,000") == 100000
    assert cents(Decimal("0.005")) == 0  # half-even: 0.5 cent -> 0
    assert cents(Decimal("0.015")) == 2  # 1.5 cent -> 2
    assert cents(None) is None
    assert cents(2500) == 2500


@pytest.mark.parametrize("bad", [1.5, True, "abc"])
def test_cents_rejects_float_bool_garbage(bad):
    with pytest.raises(MoneyError):
        cents(bad)


def test_gross_wages_t01_unknown_rate_is_none_not_zero():
    assert gross_wages(134, None) is None
    assert gross_wages(None, 2200) is None


def test_gross_wages_decimal_half_even_once():
    assert gross_wages(134, 2200) == 4913       # 4913.333.. -> 4913
    assert gross_wages(4770, 2200) == 174900
    assert gross_wages(1, 3) == 0               # 0.05 cents -> 0
    assert gross_wages(10, 3) == 0              # 0.5 -> 0 (half-even)
    assert gross_wages(30, 3) == 2              # 1.5 -> 2 (half-even)


def test_round_once_at_end_not_per_segment():
    # two segments of 0.5 cents each: per-segment rounding gives 0, round-once gives 1
    segs = [gross_wages_exact(10, 3), gross_wages_exact(10, 3)]
    assert sum(gross_wages(10, 3) for _ in range(2)) == 0
    assert to_cents(sum(segs)) == 1


def test_negative_inputs_raise():
    with pytest.raises(MoneyError):
        gross_wages(-1, 2200)


def test_sum_known_propagates_unknown():
    assert sum_known([1, 2, 3]) == 6
    assert sum_known([1, None, 3]) is None
    assert sum_known([]) == 0
