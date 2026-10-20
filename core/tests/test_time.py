import json
from pathlib import Path

import pytest

from payrollpilot_core.time import (
    DurationError,
    find_duplicates,
    find_overlaps,
    in_period,
    normalize_duration,
    weekly_minutes,
    workweek_for,
)

FIX = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "fixtures"


@pytest.mark.parametrize("text,minutes", [
    ("2h14", 134),        # T01
    ("2h 14m", 134),
    ("2H14M", 134),
    ("8h", 480),
    ("2:14", 134),
    ("2.25h", 135),
    ("0.5 hours", 30),
    ("134m", 134),
    ("0h00", 0),
])
def test_normalize_duration_valid(text, minutes):
    assert normalize_duration(text) == minutes


def test_2h14_is_not_2_14_hours():
    # 2.14 h would be 128.4 minutes; the correct reading is 134
    assert normalize_duration("2h14") == 134 != round(2.14 * 60)


@pytest.mark.parametrize("bad", ["", "abc", "2.14", "214", "2h75", "2:7", "2.123h", "-1h", None, 134])
def test_normalize_duration_invalid_raises(bad):
    with pytest.raises(DurationError):
        normalize_duration(bad)


WEEKS = [{"start": "2026-09-28", "end": "2026-10-04"}, {"start": "2026-10-05", "end": "2026-10-11"}]


def test_weekly_minutes_per_fixed_workweek_not_averaged():
    # T05: 50h in week 1 and 30h in week 2 stay separate (averaging would show 40/40)
    entries = [{"worker_id": "w", "date": f"2026-09-{d}", "duration_minutes": 600} for d in (28, 29, 30)]
    entries += [{"worker_id": "w", "date": "2026-10-01", "duration_minutes": 600},
                {"worker_id": "w", "date": "2026-10-02", "duration_minutes": 600}]
    entries += [{"worker_id": "w", "date": "2026-10-05", "duration_minutes": 900},
                {"worker_id": "w", "date": "2026-10-06", "duration_minutes": 900}]
    wk = weekly_minutes(entries, WEEKS)
    assert wk == {"2026-09-28": {"w": 3000}, "2026-10-05": {"w": 1800}}


def test_weekly_minutes_null_duration_is_unknown_not_zero():
    entries = [{"worker_id": "w", "date": "2026-10-05", "duration_minutes": 480},
               {"worker_id": "w", "date": "2026-10-06", "duration_minutes": None}]
    assert weekly_minutes(entries, WEEKS)["2026-10-05"]["w"] is None


def test_weekly_minutes_ignores_out_of_period_entries():
    entries = [{"worker_id": "w", "date": "2026-09-26", "duration_minutes": 480}]
    assert weekly_minutes(entries, WEEKS) == {"2026-09-28": {}, "2026-10-05": {}}


def test_period_boundaries_independent():
    assert workweek_for("2026-09-27", WEEKS) is None
    assert workweek_for("2026-10-04", WEEKS) == "2026-09-28"
    assert not in_period("2026-09-26", "2026-09-28", "2026-10-11")
    assert not in_period("2026-10-12", "2026-09-28", "2026-10-11")


def test_duplicate_and_overlap_helpers_on_fixture():
    snap = json.loads((FIX / "cycle_synthetic_v1.json").read_text())
    entries = snap["time_entries"]
    assert find_duplicates(entries) == [["te_0017", "te_0018"]]
    assert find_overlaps(entries) == [("te_0026", "te_0027", 60)]


def test_fixture_worker_a_weekly_totals():
    snap = json.loads((FIX / "cycle_synthetic_v1.json").read_text())
    wk = weekly_minutes(snap["time_entries"], snap["cycle"]["workweeks"])
    assert wk["2026-09-28"]["wkr_01"] == 2400
    assert wk["2026-10-05"]["wkr_01"] == 2370
    assert wk["2026-10-05"]["wkr_02"] is None  # open timer -> unknown
