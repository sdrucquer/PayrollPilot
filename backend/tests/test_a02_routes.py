"""A-02 acceptance (FR-01, FR-02, FR-08, FR-24): load, audit, exceptions, events, approvals, stop.

The audit rules are lane B's. Until ``payrollpilot_core.audit`` is installed,
these tests inject a tiny deterministic stand-in (``_mini_rules``) through the
same seam the app uses, so the route plumbing is tested, not the rules.
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
from payrollpilot.permissions import batch_version

REPO = Path(__file__).resolve().parents[2]


def _mini_rules(snapshot):
    out = []
    for te in snapshot["time_entries"]:
        refs = {"worker_id": te["worker_id"], "time_entry_ids": [te["id"]], "job_ids": [], "cost_ids": []}
        if te["job_id"] is None:
            out.append({"id": f"exc_mj_{te['id']}", "category": "missing_job", "title": f"Shift on {te['date']} has no job",
                        "observed": f"{te['duration_minutes']} min, job empty", "expected": "every paid shift maps to a job",
                        "evidence": [], "entity_refs": refs,
                        "stage_impact": {"stage1_wages": "none", "stage2_costs": "job_costing"},
                        "intended_respondent_role": "ops_lead", "next_action": "ask ops lead which job"})
        if (te["duration_minutes"] or 0) > 480:
            out.append({"id": f"exc_ls_{te['id']}", "category": "long_shift", "title": f"Shift on {te['date']} over 8h",
                        "evidence": [te["source_ref"]], "entity_refs": refs,
                        "stage_impact": {"stage1_wages": "blocks_worker", "stage2_costs": "none"},
                        "intended_respondent_role": "ops_lead"})
    return out


@pytest.fixture
def client(settings, monkeypatch):
    monkeypatch.setattr(core_bridge, "_run_audit", _mini_rules)
    monkeypatch.setattr(core_bridge, "AUDIT_MODE", "test_stub")
    c = TestClient(create_app(settings))
    c.pp = c.app.state.pp
    return c


def _load(client, name="cycle_mini_v1"):
    r = client.post("/api/cycles/load", json={"source": "fixture", "name": name})
    assert r.status_code == 200, r.text
    return r.json()


def test_load_shows_coverage_stage_states_destination(client):
    cyc = _load(client)
    assert cyc["id"] == "cyc_mini_v1"
    assert cyc["stage1"]["state"] == "not_started" and cyc["stage2"]["state"] == "not_started"
    assert cyc["destination"] == "not_prepared"
    assert len(cyc["coverage"]) == 2
    assert any(c["complete"] is False and c["incomplete_reason"] == "not_attempted" for c in cyc["coverage"])
    assert client.get("/api/cycles/cyc_mini_v1").json()["id"] == "cyc_mini_v1"
    assert client.get("/api/cycles/nope").status_code == 404


def test_reload_same_snapshot_dedupes(client):
    _load(client)
    _load(client)
    db = client.pp.db
    assert len(db.record_versions(kinds.SNAPSHOT, "cyc_mini_v1")) == 1
    types = [e["type"] for e in db.list_events(cycle_id="cyc_mini_v1")]
    assert types.count("cycle.created") == 1 and types.count("snapshot.captured") == 1


def test_load_rejects_path_tricks_and_missing(client):
    assert client.post("/api/cycles/load", json={"source": "fixture", "name": "../../etc/passwd"}).status_code == 400
    assert client.post("/api/cycles/load", json={"source": "fixture", "name": "missing"}).status_code == 404
    assert client.post("/api/cycles/load", json={"source": "web", "name": "x"}).status_code == 422


def test_audit_stores_exceptions_with_evidence_provenance_and_events(client):
    _load(client)
    body = client.post("/api/cycles/cyc_mini_v1/audit").json()
    excs = body["exceptions"]
    assert {(e["category"], tuple(e["entity_refs"]["time_entry_ids"])) for e in excs} == {
        ("missing_job", ("te_0002",)), ("long_shift", ("te_0003",))}
    for e in excs:
        assert e["evidence"], e["id"]  # back-filled from source refs when core gave none
        assert e["provenance"] == "seeded_issue"
        assert e["state"] == "detected" and e["owner_agent"] == "audit" and e["cycle_id"] == "cyc_mini_v1"
        assert e["dollars_affected_cents"] is None  # unknown stays null, never 0
    types = [ev["type"] for ev in client.get("/api/events", params={"cycle_id": "cyc_mini_v1"}).json()]
    assert "cycle.created" in types and "audit.completed" in types and types.count("exception.detected") == 2


def test_reaudit_keeps_case_state_and_does_not_redetect(client):
    _load(client)
    client.post("/api/cycles/cyc_mini_v1/audit")
    from payrollpilot.coordinator import transition_exception

    transition_exception(client.pp.db, "exc_mj_te_0002", "investigating", actor="audit", reason="test")
    excs = client.post("/api/cycles/cyc_mini_v1/audit").json()["exceptions"]
    assert {e["id"]: e["state"] for e in excs}["exc_mj_te_0002"] == "investigating"
    types = [ev["type"] for ev in client.get("/api/events", params={"cycle_id": "cyc_mini_v1"}).json()]
    assert types.count("exception.detected") == 2


def test_exception_filters_and_detail(client):
    _load(client)
    client.post("/api/cycles/cyc_mini_v1/audit")
    base = "/api/cycles/cyc_mini_v1/exceptions"
    assert len(client.get(base).json()) == 2
    assert [e["category"] for e in client.get(base, params={"stage": "stage1"}).json()] == ["long_shift"]
    assert [e["category"] for e in client.get(base, params={"stage": "stage2"}).json()] == ["missing_job"]
    assert len(client.get(base, params={"category": "missing_job"}).json()) == 1
    assert len(client.get(base, params={"state": "resolved"}).json()) == 0
    d = client.get("/api/exceptions/exc_mj_te_0002").json()
    assert d["messages"] == {"outbound": [], "inbound": []} and d["resolution"] is None and d["correction"] is None
    assert client.get("/api/exceptions/nope").status_code == 404


def test_core_contract_violation_is_not_success(client, monkeypatch):
    _load(client)
    monkeypatch.setattr(core_bridge, "_run_audit", lambda s: [{"id": "exc_bad", "category": "made_up", "title": "x"}])
    r = client.post("/api/cycles/cyc_mini_v1/audit")
    assert r.status_code == 502
    assert client.get("/api/cycles/cyc_mini_v1/exceptions").json() == []


def _seed_batch(client, text="Hi, 1 quick payroll check"):
    batch = {"id": "msg_batch_01", "cycle_id": "cyc_mini_v1", "exception_ids": ["exc_mj_te_0002"],
             "intended_respondent_role": "ops_lead", "actual_recipient": "+15550000012", "channel": "imessage",
             "text": text, "text_hash": "sha256:x", "state": "draft", "approval_id": None, "provenance": "real"}
    client.pp.db.put_record(kinds.MESSAGE_BATCH, batch)
    return batch


def test_approval_binds_to_current_version(client):
    _load(client)
    b = _seed_batch(client)
    v = batch_version(b)
    stale = client.post("/api/approvals", json={"kind": "message_send", "target_id": b["id"], "target_version": "sha256:old", "scope_text": "send"})
    assert stale.status_code == 409 and stale.json()["current_version"] == v
    ok = client.post("/api/approvals", json={"kind": "message_send", "target_id": b["id"], "target_version": v,
                                              "scope_text": "Send this exact text to the allowlisted test recipient"})
    assert ok.status_code == 200, ok.text
    appr = ok.json()
    assert appr["state"] == "active" and appr["target_version"] == v
    stored = client.pp.db.get_record(kinds.MESSAGE_BATCH, b["id"])
    assert stored["approval_id"] == appr["id"] and stored["state"] == "approved"
    # a second approval supersedes the first
    again = client.post("/api/approvals", json={"kind": "message_send", "target_id": b["id"], "target_version": v, "scope_text": "send"}).json()
    assert client.pp.db.get_approval(appr["id"])["state"] == "invalidated"
    assert client.pp.db.get_approval(again["id"])["state"] == "active"
    types = [e["type"] for e in client.get("/api/events").json()]
    assert "approval.granted" in types and "approval.invalidated" in types


def test_gated_approval_kinds_are_unavailable(client):
    r = client.post("/api/approvals", json={"kind": "source_write", "target_id": "x", "target_version": "sha256:x", "scope_text": "x"})
    assert r.status_code == 501 and r.json()["error"] == "gated"
    r = client.post("/api/approvals", json={"kind": "payroll_draft", "target_id": "x", "target_version": "sha256:x", "scope_text": "x"})
    assert r.status_code == 501


def test_run_stop_blocks_new_actions_and_keeps_approvals(client):
    _load(client)
    b = _seed_batch(client)
    appr = client.post("/api/approvals", json={"kind": "message_send", "target_id": b["id"], "target_version": batch_version(b), "scope_text": "send"}).json()
    assert client.post("/api/run/stop").json() == {"stopped": True}
    assert client.post("/api/cycles/cyc_mini_v1/audit").status_code == 409
    assert client.pp.db.get_approval(appr["id"])["state"] == "active"
    assert client.get("/api/health").json()["run_stopped"] is True
    assert client.post("/api/run/stop", json={"resume": True}).json() == {"stopped": False}
    assert client.post("/api/cycles/cyc_mini_v1/audit").status_code == 200


def test_state_survives_restart(settings, monkeypatch):
    monkeypatch.setattr(core_bridge, "_run_audit", _mini_rules)
    c1 = TestClient(create_app(settings))
    _load(c1)
    c1.post("/api/cycles/cyc_mini_v1/audit")
    c1.app.state.pp.db.close()
    c2 = TestClient(create_app(settings))
    assert len(c2.get("/api/cycles/cyc_mini_v1/exceptions").json()) == 2
    assert c2.get("/api/cycles/cyc_mini_v1").json()["id"] == "cyc_mini_v1"


# ---- lane B fixture (runs once the fixture is in this checkout) -------------------
SYNTH = REPO / "docs" / "contracts" / "fixtures" / "cycle_synthetic_v1.json"
EXPECTED = REPO / "docs" / "contracts" / "fixtures" / "expected_exceptions_v1.json"


@pytest.mark.skipif(not SYNTH.exists(), reason="lane B fixture not on this branch yet")
def test_loads_lane_b_synthetic_cycle(settings, tmp_path):
    shutil.copy(SYNTH, tmp_path / SYNTH.name)
    c = TestClient(create_app(dataclasses.replace(settings, fixtures_dir=tmp_path)))
    cyc = _load(c, "cycle_synthetic_v1")
    assert cyc["id"] == "cyc_synth_v1" and cyc["destination"] == "not_prepared" and cyc["coverage"]


@pytest.mark.skipif(not (SYNTH.exists() and EXPECTED.exists() and core_bridge.AUDIT_MODE == "core"),
                    reason="needs lane B fixture + payrollpilot_core.audit installed")
def test_audit_matches_expected_exceptions(settings, tmp_path):
    shutil.copy(SYNTH, tmp_path / SYNTH.name)
    c = TestClient(create_app(dataclasses.replace(settings, fixtures_dir=tmp_path)))
    _load(c, "cycle_synthetic_v1")
    got = c.post("/api/cycles/cyc_synth_v1/audit").json()["exceptions"]
    want = json.loads(EXPECTED.read_text())["exceptions"]
    key = lambda e: (e["category"], e["entity_refs"].get("worker_id"), tuple(sorted(e["entity_refs"].get("time_entry_ids") or [])),
                     tuple(sorted(e["entity_refs"].get("job_ids") or [])), tuple(sorted(e["entity_refs"].get("cost_ids") or [])))
    assert {key(e) for e in got} == {key(e) for e in want}
    assert all(e["evidence"] and e["provenance"] for e in got)
