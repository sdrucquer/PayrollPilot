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


def _t02_impact(kind, before, after, snapshot, resolution_id=None):
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


def test_core_dependent_routes_return_501_until_lane_b(env, monkeypatch):
    c, _ = env
    for name in ("propose_correction", "cycle_readiness", "build_packet", "build_workbook"):
        monkeypatch.setattr(core_bridge, name, None)
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


SYNTH = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "fixtures" / "cycle_synthetic_v1.json"


@pytest.mark.skipif(core_bridge.cycle_readiness is None or not SYNTH.exists(),
                    reason="needs payrollpilot_core.readiness.cycle_readiness + lane B fixture")
def test_readiness_route_uses_core_on_synthetic_cycle(settings, tmp_path):
    shutil.copy(SYNTH, tmp_path / SYNTH.name)
    c = TestClient(create_app(dataclasses.replace(settings, fixtures_dir=tmp_path)))
    c.post("/api/cycles/load", json={"source": "fixture", "name": "cycle_synthetic_v1"})
    c.post("/api/cycles/cyc_synth_v1/audit")
    body = c.get("/api/cycles/cyc_synth_v1/readiness").json()
    assert body["stage1"]["state"] in {"ready", "partial", "pending", "blocked", "not_meaningful"}
    kinds_seen = {i["kind"] for i in body["items"]}
    assert "manager_pool" in kinds_seen
    for item in body["items"]:
        assert item["readiness"]["state"] in {"ready", "partial", "pending", "blocked", "not_meaningful"}
        if item["readiness"]["state"] != "ready":
            assert item["readiness"]["blockers"] or item["readiness"]["state"] == "not_meaningful", item["id"]


class _CoreErr(ValueError):
    def __init__(self, code):
        super().__init__(f"{code}: test")
        self.code = code


@pytest.mark.parametrize("code,status", [("stale_before", 409), ("allocation_mismatch", 409),
                                         ("unsupported:identity_merge", 422), ("target_not_found", 404)])
def test_core_correction_error_codes_map_to_http(env, monkeypatch, code, status):
    c, _ = env

    def boom(*a, **k):
        raise _CoreErr(code)

    monkeypatch.setattr(core_bridge, "propose_correction", boom)
    r = c.post("/api/corrections", json={"kind": "job_allocation", "cycle_id": "cyc_mini_v1",
                                         "after": {"time_entry_id": "te_0002", "job_id": "job_01"}})
    assert r.status_code == status and r.json()["error"] == code


def test_workbook_verification_failure_is_not_success(env, monkeypatch):
    c, _ = env

    class WorkbookVerificationError(RuntimeError):
        pass

    def bad_wb(packet, path):
        raise WorkbookVerificationError("Review total mismatch")

    monkeypatch.setattr(core_bridge, "build_packet", lambda **k: {"draft_version": "x"})
    monkeypatch.setattr(core_bridge, "build_workbook", bad_wb)
    r = c.post("/api/cycles/cyc_mini_v1/workbook")
    assert r.status_code == 500 and r.json()["error"] == "workbook_verification_failed"
    types = [e["type"] for e in c.get("/api/events", params={"cycle_id": "cyc_mini_v1"}).json()]
    assert "workbook.generated" not in types and "workbook.verified" not in types


MATRIX = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "fixtures" / "readiness_matrix_v1.json"


@pytest.mark.skipif(core_bridge.propose_correction is None or core_bridge.cycle_readiness is None or not SYNTH.exists(),
                    reason="needs payrollpilot_core corrections + readiness and lane B fixtures")
def test_t02_end_to_end_wages_unchanged_job_costing_changed(settings, tmp_path):
    """T02 through the routes with real lane B core: te_0014 job_01 -> job_02."""
    shutil.copy(SYNTH, tmp_path / SYNTH.name)
    c = TestClient(create_app(dataclasses.replace(settings, fixtures_dir=tmp_path)))
    c.post("/api/cycles/load", json={"source": "fixture", "name": "cycle_synthetic_v1"})
    c.post("/api/cycles/cyc_synth_v1/audit")
    before_ready = c.get("/api/cycles/cyc_synth_v1/readiness").json()
    r = c.post("/api/corrections", json={"kind": "job_allocation", "cycle_id": "cyc_synth_v1",
                                         "after": {"time_entry_id": "te_0014", "job_id": "job_02"}})
    assert r.status_code == 200, r.text
    corr = r.json()
    assert corr["before"] == {"time_entry_id": "te_0014", "job_id": "job_01"}
    impact = corr["calculation_impact"]
    assert impact["stage1_wages_delta_cents"] == 0
    deltas = {d["job_id"]: d["labor_delta_cents"] for d in impact["job_costing_delta"]}
    assert deltas.get("job_02") and deltas["job_02"] > 0 and deltas.get("job_01") == -deltas["job_02"]
    appr = c.post("/api/approvals", json={"kind": "local_correction", "target_id": corr["id"],
                                          "target_version": corr["target_version"], "scope_text": "Move te_0014 to job_02 locally"})
    assert appr.status_code == 200, appr.text
    out = c.post(f"/api/corrections/{corr['id']}/apply")
    assert out.status_code == 200, out.text
    changed = {ch["scope"] for ch in out.json()["readiness_changes"]}
    assert "stage1" not in changed  # wages readiness untouched by an allocation-only correction
    after_ready = c.get("/api/cycles/cyc_synth_v1/readiness").json()
    assert after_ready["stage1"]["state"] == before_ready["stage1"]["state"]
    if MATRIX.exists():
        want = json.loads(MATRIX.read_text())["after_t02_correction"]
        assert after_ready["stage1"]["state"] == want["stage1"]["state"]
        assert after_ready["stage1"]["scope"] == want["stage1"]["scope"]
    types = [e["type"] for e in c.get("/api/events", params={"cycle_id": "cyc_synth_v1"}).json()]
    assert {"correction.proposed", "approval.granted", "correction.applied", "recalc.completed"} <= set(types)
    # The fixed exception is resolved (lane F repro) and only its blocker clears from the quote card.
    excs = {e["id"]: e for e in c.get("/api/cycles/cyc_synth_v1/exceptions").json()}
    apa = [e for e in excs.values() if e["category"] == "already_paid_allocation"]
    assert apa and all(e["state"] == "resolved" for e in apa)
    assert set(out.json()["resolved_exception_ids"]) == {e["id"] for e in apa}
    q = lambda body: {b["code"] for i in body["items"] if i["id"] == "ci_quote_job_01" for b in i["readiness"]["blockers"]}
    assert q(after_ready) == q(before_ready) - {f"exception:{e['id']}" for e in apa}
    assert q(after_ready) < q(before_ready)
    # Unrelated open cases stay open
    assert sum(1 for e in excs.values() if e["state"] == "resolved") == len(apa)


@pytest.mark.skipif(core_bridge.build_packet is None or core_bridge.build_workbook is None or not SYNTH.exists(),
                    reason="needs payrollpilot_core packet + workbook (lane B B-04)")
def test_packet_and_workbook_routes_with_real_core(settings, tmp_path):
    shutil.copy(SYNTH, tmp_path / SYNTH.name)
    s = dataclasses.replace(settings, fixtures_dir=tmp_path, private_snapshots_dir=tmp_path / "private" / "snapshots")
    c = TestClient(create_app(s))
    c.post("/api/cycles/load", json={"source": "fixture", "name": "cycle_synthetic_v1"})
    c.post("/api/cycles/cyc_synth_v1/audit")
    pkt = c.get("/api/cycles/cyc_synth_v1/packet")
    assert pkt.status_code == 200, pkt.text
    wb = c.post("/api/cycles/cyc_synth_v1/workbook")
    assert wb.status_code == 200, wb.text
    art = wb.json()
    assert art["original_updated"] is False and art["verified_totals"]
    assert Path(art["path"]).is_file() and str(tmp_path) in art["path"]  # written under the private dir, not the repo
    types = [e["type"] for e in c.get("/api/events", params={"cycle_id": "cyc_synth_v1"}).json()]
    assert "workbook.generated" in types and "workbook.verified" in types


def test_resolved_case_reopens_only_on_source_change(env):
    from payrollpilot.coordinator import resolve_by_applied_correction

    c, fx = env
    db = c.app.state.pp.db
    corr = {"id": "corr_x", "state": "applied", "approval_id": "appr_x",
            "before": {"time_entry_id": "te_0003"}, "after": {"time_entry_id": "te_0003"}}
    assert resolve_by_applied_correction(db, "exc_ls_te_0003", corr)["state"] == "resolved"
    # unchanged re-detection: stays resolved
    c.post("/api/cycles/cyc_mini_v1/audit")
    assert db.get_record(kinds.EXCEPTION, "exc_ls_te_0003")["state"] == "resolved"
    # source change alters the detection content -> reopened
    snap = json.loads((fx / FIX.name).read_text())
    te = next(t for t in snap["time_entries"] if t["id"] == "te_0003")
    te["duration_minutes"], te["version_hash"] = 600, "sha256:mini3-edited"
    (fx / FIX.name).write_text(json.dumps(snap))
    monkey_rules = core_bridge._run_audit

    def rules(snapshot):
        out = monkey_rules(snapshot)
        for e in out:
            if e["id"] == "exc_ls_te_0003":
                e["observed"] = f"{te['duration_minutes']} min"
        return out

    core_bridge._run_audit = rules
    try:
        c.post("/api/cycles/cyc_mini_v1/load".replace("/cyc_mini_v1", ""), json={"source": "fixture", "name": "cycle_mini_v1"})
        c.post("/api/cycles/cyc_mini_v1/audit")
    finally:
        core_bridge._run_audit = monkey_rules
    assert db.get_record(kinds.EXCEPTION, "exc_ls_te_0003")["state"] == "detected"


def test_resolve_by_correction_refuses_unrelated_or_unapplied(env):
    from payrollpilot.coordinator import resolve_by_applied_correction

    c, _ = env
    db = c.app.state.pp.db
    unrelated = {"id": "corr_y", "state": "applied", "approval_id": "a", "before": {"time_entry_id": "te_0001"}, "after": {"time_entry_id": "te_0001"}}
    assert resolve_by_applied_correction(db, "exc_mj_te_0002", unrelated) is None
    unapplied = dict(unrelated, state="approved", before={"time_entry_id": "te_0002"}, after={"time_entry_id": "te_0002"})
    assert resolve_by_applied_correction(db, "exc_mj_te_0002", unapplied) is None
    assert db.get_record(kinds.EXCEPTION, "exc_mj_te_0002")["state"] == "detected"
