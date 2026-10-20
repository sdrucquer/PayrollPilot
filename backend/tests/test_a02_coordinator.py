from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from payrollpilot import coordinator, kinds
from payrollpilot.app import create_app
from payrollpilot.db import Database


def _exc(db):
    db.put_record(kinds.EXCEPTION, {"id": "exc_1", "cycle_id": "cyc_x", "state": "detected"})


def test_transition_accepts_dict_or_id_and_emits_event(tmp_path):
    db = Database(tmp_path / "c.db")
    _exc(db)
    out = coordinator.transition(db, "exc_1", "investigating", "audit")
    assert out["state"] == "investigating"
    out = coordinator.transition(db, out, "awaiting_reply", "resolution", next_action="wait for reply")
    assert out["state"] == "awaiting_reply" and out["next_action"] == "wait for reply"
    assert [e["type"] for e in db.list_events("cyc_x")] == ["exception.state_changed"] * 2


def test_transition_rejects_skips_and_allows_escape_states(tmp_path):
    db = Database(tmp_path / "c.db")
    _exc(db)
    with pytest.raises(coordinator.TransitionRejected):
        coordinator.transition(db, "exc_1", "resolved", "resolution")
    assert coordinator.transition(db, "exc_1", "escalated", "owner")["state"] == "escalated"
    with pytest.raises(KeyError):
        coordinator.transition(db, "exc_missing", "investigating", "audit")


def test_health_reports_comms_routes_absent(settings):
    body = TestClient(create_app(settings)).get("/api/health").json()
    assert body["routes"]["comms"] == "absent"
