"""A-01 acceptance (FR-25): records and events survive a process restart."""

from __future__ import annotations

from fastapi.testclient import TestClient

from payrollpilot.app import create_app
from payrollpilot.db import Database
from payrollpilot.events import emit


def test_records_and_events_survive_restart(tmp_path):
    path = tmp_path / "restart.db"
    db1 = Database(path)
    db1.put_record("worker", {"id": "wkr_01", "display_name": "Worker A", "provenance": "synthetic"})
    db1.put_record("worker", {"id": "wkr_01", "display_name": "Worker A (v2)", "provenance": "synthetic"})
    emit(db1, type="cycle.created", actor="system", cycle_id="cyc_t", summary="created")
    db1.approvals_for_target("x")
    assert db1.claim_inbound("pm_1", "msg_in_1") is True
    assert db1.claim_send("msg_batch_1") is True
    db1.close()

    db2 = Database(path)  # simulated restart: new connection, same file
    latest = db2.get_record("worker", "wkr_01")
    assert latest["display_name"] == "Worker A (v2)"
    assert latest["_version"] == 2
    assert [v["display_name"] for v in db2.record_versions("worker", "wkr_01")] == ["Worker A", "Worker A (v2)"]
    events = db2.list_events(cycle_id="cyc_t")
    assert [e["type"] for e in events] == ["cycle.created"]
    # dedupe and send-once survive restart (FR-25: retries cannot duplicate SMS)
    assert db2.claim_inbound("pm_1", "msg_in_1") is False
    assert db2.claim_send("msg_batch_1") is False
    db2.close()


def test_null_money_stays_null(tmp_path):
    db = Database(tmp_path / "n.db")
    db.put_record("cost", {"id": "cost_01", "amount_cents": None, "provenance": "synthetic"})
    assert db.get_record("cost", "cost_01")["amount_cents"] is None


def test_health_reports_contract_and_adapter_modes(settings):
    client = TestClient(create_app(settings))
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["contract_version"] == "1"
    assert set(body["integrations"]) == {"photon", "band", "cognee", "browser_use"}
    assert set(body["integrations"].values()) <= {"tested", "unverified", "blocked"}
    assert body["adapters"]["messaging"]["mode"] == "fake"
    assert "FAKE" in body["adapters"]["messaging"]["label"]
    assert body["adapters"]["audit"] in {"core", "stub"}


def test_unknown_event_type_rejected(tmp_path):
    import pytest

    db = Database(tmp_path / "e.db")
    with pytest.raises(ValueError):
        emit(db, type="payroll.submitted", actor="system", summary="nope")
