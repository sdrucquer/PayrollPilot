"""A-04 acceptance (FR-13, FR-14, T02, T16) for the lane A parts.

Lane B's propose_correction / readiness / packet / workbook are not merged yet.
Routes return 501 without them (tested). The apply path is tested with a
stand-in propose_correction that returns a fixed T02-shaped impact; the real
impact numbers are lane B's to test.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from payrollpilot import core_bridge, kinds
from payrollpilot.app import create_app

from .test_a02_routes import _mini_rules

FIX = Path(__file__).parent / "fixtures" / "cycle_mini_v1.json"


def _t02_impact(kind, before, after, snapshot):
    return {"calculation_impact": {"stage1_wages_delta_cents": 0,
                                   "job_costing_delta": [{"job_id": after.get("job_id"), "labor_delta_cents": None}]}}


@pytest.fixture
def env(settings, monkeypatch, tmp_path):
    fx = tmp_path / "fx"
    fx.mkdir()
    shutil.copy(FIX, fx / FIX.name)
    monkeypatch.setattr(core_bridge, "_run_audit", _mini_rules)
    s = dataclasses.replace(settings, fixtures_dir=fx)
    c = TestClient(create_app(s))
    c.post("/api/cycles/load", json={"source": "fixture", "name": "cycle_mini_v1"})
    c.post("/api/cycles/cyc_mini_v1/audit")
    return c, fx


def _propose(c):
    r = c.post("/api/corrections", json={"kind": "job_allocation", "cycle_id": "cyc_mini_v1",
                                         "after": {"time_entry_id": "te_0002", "job_id": "job_01"}})
    assert r.status_code == 200, r.text
    return r.json()


def _approve(c, corr, version=None):
    return c.post("/api/approvals", json={"kind": "local_correction", "target_id": corr["id"],
                                          "target_version": version or corr["target_version"],
                                          "scope_text": "Allocate te_0002 to job_01 locally"})


def test_core_dependent_routes_return_501_until_lane_b(env):
    c, _ = env
    r = c.post("/api/corrections", json={"kind": "job_allocation", "cycle_id": "cyc_mini_v1",
                                         "after": {"time_entry_id": "te_0002", "job_id": "job_01"}})
    assert r.status_code == 501 and r.json()["reason"]
    for method, path in [("get", "/api/cycles/cyc_mini_v1/readiness"), ("get", "/api/cycles/cyc_mini_v1/packet"),
                         ("post", "/api/cycles/cyc_mini_v1/workbook")]:
        r = getattr(c, method)(path)
        assert r.status_code == 501 and r.json()["reason"] == "core not merged", path
    assert c.get("/api/cycles/nope/readiness").status_code == 404


def test_apply_requires_approval_then_applies_locally(env, monkeypatch):
    c, _ = env
    monkeypatch.setattr(core_bridge, "propose_correction", _t02_impact)
    corr = _propose(c)
    assert corr["before"] == {"time_entry_id": "te_0002", "job_id": None}
    assert corr["calculation_impact"]["stage1_wages_delta_cents"] == 0
    assert c.post(f"/api/corrections/{corr['id']}/apply").status_code == 403  # no approval
    assert _approve(c, corr, "sha256:stale").status_code == 409
    assert _approve(c, corr).status_code == 200
    r = c.post(f"/api/corrections/{corr['id']}/apply")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["correction"]["state"] == "applied"
    # corrected view: te_0002 now has a job, so missing_job is not re-detected; source snapshot unchanged
    assert "exc_mj_te_0002" not in {e["id"] for e in body["exceptions"]}
    raw = c.app.state.pp.db.get_record(kinds.SNAPSHOT, "cyc_mini_v1")["data"]
    assert next(te for te in raw["time_entries"] if te["id"] == "te_0002")["job_id"] is None
    types = [e["type"] for e in c.get("/api/events", params={"cycle_id": "cyc_mini_v1"}).json()]
    assert {"correction.proposed", "approval.granted", "correction.applied", "recalc.completed"} <= set(types)
    assert c.post(f"/api/corrections/{corr['id']}/apply").status_code == 409  # applies once


def test_source_change_after_approval_invalidates_it(env, monkeypatch):
    """T16: mutate the time entry version after approval -> approval.invalidated, apply refused."""
    c, fx = env
    monkeypatch.setattr(core_bridge, "propose_correction", _t02_impact)
    corr = _propose(c)
    appr = _approve(c, corr).json()
    snap = json.loads((fx / FIX.name).read_text())
    te = next(t for t in snap["time_entries"] if t["id"] == "te_0002")
    te["version_hash"] = "sha256:mini2-edited-in-source"
    te["duration_minutes"] = 150
    (fx / FIX.name).write_text(json.dumps(snap))
    assert c.post("/api/cycles/load", json={"source": "fixture", "name": "cycle_mini_v1"}).status_code == 200
    db = c.app.state.pp.db
    assert db.get_approval(appr["id"])["state"] == "invalidated"
    assert db.get_record(kinds.CORRECTION, corr["id"])["state"] == "invalidated"
    events = c.get("/api/events", params={"cycle_id": "cyc_mini_v1"}).json()
    assert any(e["type"] == "approval.invalidated" and e["refs"]["approval_id"] == appr["id"] for e in events)
    r = c.post(f"/api/corrections/{corr['id']}/apply")
    assert r.status_code == 403
