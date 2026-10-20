"""A-03 transform + dedupe (FR-02, FR-07, T13). No network: the agent output
below is a made-up stand-in with placeholder names."""

from __future__ import annotations

import dataclasses
import json

from fastapi.testclient import TestClient

from payrollpilot.adapters import browser_use as bu
from payrollpilot.app import create_app

OUT = {
    "time_entries": [
        {"jobber_id": "111", "url": None, "worker_name": "Placeholder One", "date": "2026-09-29", "start_time": "08:00",
         "end_time": "10:14", "duration_text": "2h14", "job_title": None, "job_number": None, "approved": True, "timer_running": False},
        {"jobber_id": "112", "worker_name": "Placeholder One", "date": "2026-09-30", "start_time": "07:00", "end_time": None,
         "duration_text": None, "job_title": "Lawn install", "job_number": "J-7", "approved": False, "timer_running": True},
        {"jobber_id": None, "worker_name": "Placeholder Two", "date": "2026-10-06", "start_time": "07:00", "end_time": "16:20",
         "duration_text": "9h20", "job_title": "Lawn install", "job_number": "J-7", "approved": True},
    ],
    "jobs": [{"title": "Lawn install", "job_number": "J-7", "jobber_id": "j7"}],
    "workers": [{"name": "Placeholder One", "jobber_id": "u1"}, {"name": "Placeholder Two"}],
    "coverage": {"all_pages_viewed": False, "entries_seen": 3, "total_shown_by_jobber": 5, "problems": None},
}


def _snap(out=OUT):
    return bu.to_snapshot(out, start="2026-09-28", end="2026-10-11", run_id="run_test", captured_at="2026-10-20T13:30:00-07:00")


def test_snapshot_shape_deidentified_and_honest():
    s = _snap()
    assert s["provenance"] == "real" and s["cycle"]["provenance"] == "real"
    assert [w["display_name"] for w in s["workers"]] == ["Worker A", "Worker B"]
    assert all(j["display_name"].startswith("Job ") for j in s["jobs"])
    te = {t["source_ref"]["record_id"]: t for t in s["time_entries"]}
    assert te["111"]["duration_minutes"] == 134 and te["111"]["job_id"] is None
    assert te["112"]["duration_minutes"] is None and te["112"]["open_timer"] is True  # unknown stays null
    assert te["111"]["start"].endswith("-04:00")  # business tz offset
    cov = {r["dataset"]: r for r in s["cycle"]["coverage"]}
    assert cov["time_entries"]["complete"] is False and cov["time_entries"]["incomplete_reason"] == "pagination_cut"  # not all pages
    assert cov["time_entries"]["method"] == "browser_use" and cov["time_entries"]["record_count"] == 3
    assert cov["rates"]["incomplete_reason"] == "not_attempted"
    assert [w["start"] for w in s["cycle"]["workweeks"]] == ["2026-09-28", "2026-10-05"]


def test_complete_only_when_all_pages_and_counts_match():
    out = json.loads(json.dumps(OUT))
    out["coverage"] = {"all_pages_viewed": True, "entries_seen": 3, "total_shown_by_jobber": 3, "problems": None}
    assert {r["dataset"]: r for r in _snap(out)["cycle"]["coverage"]}["time_entries"]["complete"] is True


def test_second_read_dedupes_by_source_id():
    a = _snap()
    b = _snap()
    merged = bu.merge_snapshots(a, b)
    assert len(merged["time_entries"]) == len(a["time_entries"]) == 3


def test_private_snapshot_loads_and_audits(settings, tmp_path):
    snaps = tmp_path / "snapshots"
    snaps.mkdir()
    (snaps / "jobber_2026-09-28_2026-10-11.json").write_text(json.dumps(_snap()))
    c = TestClient(create_app(dataclasses.replace(settings, private_snapshots_dir=snaps)))
    r = c.post("/api/cycles/load", json={"source": "private_snapshot", "name": "jobber_2026-09-28_2026-10-11"})
    assert r.status_code == 200, r.text
    cyc = r.json()
    assert cyc["provenance"] == "real" and cyc["id"] == "cyc_jobber_20260928_20261011"
    a = c.post(f"/api/cycles/{cyc['id']}/audit")
    assert a.status_code == 200, a.text
    assert all(e["provenance"] == "real" and e["evidence"] for e in a.json()["exceptions"])


def test_dry_run_makes_no_call(monkeypatch, capsys):
    monkeypatch.setattr(bu, "_call", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network call in dry run")))
    assert bu.main(["read", "--start", "2026-09-28", "--end", "2026-10-11", "--dry-run"]) == 0
    assert '"dry_run": true' in capsys.readouterr().out


def test_all_pages_but_no_source_total_is_incomplete_without_pagination_claim():
    out = json.loads(json.dumps(OUT))
    out["coverage"] = {"all_pages_viewed": True, "entries_seen": 3, "total_shown_by_jobber": None,
                       "problems": "approval state not shown in this view"}
    row = {r["dataset"]: r for r in _snap(out)["cycle"]["coverage"]}["time_entries"]
    assert row["complete"] is False and row["incomplete_reason"] is None
    assert "no total" in row["filters"]["incomplete_detail"]


def test_same_name_on_two_profiles_flags_duplicate_profiles():
    out = json.loads(json.dumps(OUT))
    out["workers"].append({"name": "Placeholder Two", "jobber_id": None})
    w = {x["source_name"]: x for x in _snap(out)["workers"]}
    assert w["Placeholder Two"]["identity_status"] == "duplicate_profiles"
    assert w["Placeholder One"]["identity_status"] == "unmatched"
