"""Time helpers. Integer minutes; "2h14" is 134 minutes, never 2.14 hours.

Weekly totals are per fixed workweek (never averaged across the biweekly period).
"""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable


class DurationError(ValueError):
    pass


_HM = re.compile(r"^\s*(\d+)\s*h\s*(?:(\d{1,2})\s*m?)?\s*$", re.IGNORECASE)          # 2h14, 2h 14m, 8h
_COLON = re.compile(r"^\s*(\d+):([0-5]\d)\s*$")                                      # 2:14
_DEC_H = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hours?)\s*$", re.IGNORECASE)  # 2.25h
_MIN = re.compile(r"^\s*(\d+)\s*(?:m|min|mins|minutes?)\s*$", re.IGNORECASE)         # 134m


def normalize_duration(text: str) -> int:
    """Parse a duration string into integer minutes. Raises DurationError when invalid or inexact.

    Accepted: "2h14" / "2h 14m" / "8h" -> h+m; "2:14" -> h:mm; "2.25h" -> decimal hours
    (must resolve to whole minutes); "134m" -> minutes. Bare numbers are ambiguous and rejected.
    """
    if not isinstance(text, str):
        raise DurationError(f"duration must be a string, got {type(text).__name__}")
    m = _HM.match(text)
    if m:
        hours, mins = int(m.group(1)), int(m.group(2) or 0)
        if mins >= 60:
            raise DurationError(f"minutes component >= 60 in {text!r}")
        return hours * 60 + mins
    m = _COLON.match(text)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = _DEC_H.match(text)
    if m:
        try:
            minutes = Decimal(m.group(1)) * 60
        except InvalidOperation as e:  # pragma: no cover - regex guards this
            raise DurationError(text) from e
        if minutes != minutes.to_integral_value():
            raise DurationError(f"{text!r} is not a whole number of minutes")
        return int(minutes)
    m = _MIN.match(text)
    if m:
        return int(m.group(1))
    raise DurationError(f"unrecognized duration: {text!r}")


def _d(value: str | date) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)


def workweek_for(entry_date: str | date, workweeks: list[dict]) -> str | None:
    """Return the start date (ISO) of the fixed workweek containing entry_date, or None if outside all."""
    d = _d(entry_date)
    for wk in workweeks:
        if _d(wk["start"]) <= d <= _d(wk["end"]):
            return wk["start"] if isinstance(wk["start"], str) else wk["start"].isoformat()
    return None


def in_period(entry_date: str | date, start: str | date, end: str | date) -> bool:
    """Both cycle boundaries applied independently (T27)."""
    d = _d(entry_date)
    return _d(start) <= d <= _d(end)


def weekly_minutes(entries: Iterable[dict], workweeks: list[dict]) -> dict[str, dict[str, int | None]]:
    """{workweek_start: {worker_id: minutes}}. Entries outside every workweek are ignored here (the audit
    reports them). A null duration makes that worker's week None (unknown), never 0-filled."""
    out: dict[str, dict[str, int | None]] = {wk["start"]: {} for wk in workweeks}
    for e in entries:
        wk = workweek_for(e["date"], workweeks)
        if wk is None:
            continue
        bucket = out[wk]
        wid = e["worker_id"]
        dur = e.get("duration_minutes")
        if dur is None or bucket.get(wid, 0) is None:
            bucket[wid] = None
        else:
            bucket[wid] = bucket.get(wid, 0) + dur
    return out


def _ts(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def overlap_minutes(a: dict, b: dict) -> int:
    """Minutes two entries overlap (0 if none or if either lacks start/end)."""
    a0, a1, b0, b1 = _ts(a.get("start")), _ts(a.get("end")), _ts(b.get("start")), _ts(b.get("end"))
    if None in (a0, a1, b0, b1):
        return 0
    lo, hi = max(a0, b0), min(a1, b1)
    return max(0, int((hi - lo).total_seconds() // 60))


def _dup_key(e: dict) -> tuple:
    return (e["worker_id"], e.get("job_id"), e["date"], e.get("start"), e.get("end"), e.get("duration_minutes"))


def find_duplicates(entries: Iterable[dict]) -> list[list[str]]:
    """Groups (sorted id lists) of entries identical in worker, job, date, start, end and duration."""
    groups: dict[tuple, list[str]] = {}
    for e in entries:
        groups.setdefault(_dup_key(e), []).append(e["id"])
    return sorted(sorted(ids) for ids in groups.values() if len(ids) > 1)


def find_overlaps(entries: Iterable[dict]) -> list[tuple[str, str, int]]:
    """(id_a, id_b, minutes) for same-worker entries that overlap, excluding exact duplicates."""
    by_worker: dict[str, list[dict]] = {}
    for e in entries:
        by_worker.setdefault(e["worker_id"], []).append(e)
    out = []
    for items in by_worker.values():
        items = sorted(items, key=lambda x: x["id"])
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if _dup_key(a) == _dup_key(b):
                    continue
                m = overlap_minutes(a, b)
                if m > 0:
                    out.append((a["id"], b["id"], m))
    return sorted(out)


def format_minutes(minutes: int | None) -> str:
    if minutes is None:
        return "unknown"
    return f"{minutes // 60}h{minutes % 60:02d}m"
