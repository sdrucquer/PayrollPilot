"""Lane E demo story on the synthetic cycle: batch {already_paid_allocation, offsite_link}; owner says "yes"
(ambiguous -> clarification), then answers; later disposal cost on job_03 recalls the off-site link.
Model calls use a STUB transport; messaging is FakeMessaging (dev). Live runs are in INTEGRATION-FINDINGS."""
import asyncio
import dataclasses
import json
from pathlib import Path

from fastapi.testclient import TestClient

from payrollpilot.agents.llm import Budget, OpenRouterLLM
from payrollpilot.app import create_app
from payrollpilot.memory.base import InMemoryMemory
from payrollpilot.routes_comms import _comms

from .test_c05_routes import FakeBand

FIX = Path(__file__).resolve().parents[2] / "docs/contracts/fixtures"
EXP = {e["category"]: e for e in json.loads((FIX / "expected_exceptions_v1.json").read_text())["exceptions"]}
APA, OFF = EXP["already_paid_allocation"], EXP["offsite_link"]


def _stub(body, headers):
    user = body["messages"][1]["content"]
    assert "job_02: Job 02 (patio build)" in user  # parser sees job names
    ans = [{"exception_id": APA["id"], "status": "answered", "job_number": 2, "note": "patio build", "confidence": 0.9,
            "quote": "The Oct 1 shift was Job 02, the patio build"},
           {"exception_id": OFF["id"], "status": "answered", "job_number": 2, "note": "parent is patio job", "confidence": 0.85,
            "quote": "The disposal run on Job 03 was for the patio job too"}]
    return {"model": "stub", "usage": {"prompt_tokens": 1, "completion_tokens": 1, "cost": 0},
            "choices": [{"message": {"content": json.dumps({"answers": ans})}}]}


def test_demo_story(settings, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    settings = dataclasses.replace(settings, bridge_token="tok", fixtures_dir=FIX, band_mode="null", memory_mode="inmemory")
    c = TestClient(create_app(settings))
    cyc = c.post("/api/cycles/load", json={"source": "fixture", "name": "cycle_synthetic_v1"})
    assert cyc.status_code == 200, cyc.text
    cid = cyc.json()["id"]
    db = c.app.state.pp.db
    for e in (APA, OFF):
        if db.get_record("exception", e["id"]) is None:
            db.put_record("exception", {**{k: v for k, v in e.items() if k != "note"}, "cycle_id": cid, "state": "detected",
                                        "owner_agent": "audit", "provenance": "synthetic", "evidence": [], "message_ids": []})
    class R: app = c.app
    comms = _comms(R)
    comms.update(band=FakeBand(), memory=InMemoryMemory(), llm_cheap=OpenRouterLLM(transport=_stub, budget=Budget(1.0)))

    def approve_and_send(b):
        c.post("/api/approvals", json={"kind": "message_send", "target_id": b["id"], "target_version": b["target_version"],
                                        "scope_text": "send exact text"}).raise_for_status()
        assert c.post(f"/api/messages/{b['id']}/send").json()["state"] == "sent"

    for e in (APA, OFF):
        assert c.post(f"/api/exceptions/{e['id']}/handoff").status_code == 200
    b = c.post("/api/messages/draft", json={"exception_ids": [APA["id"], OFF["id"]]}).json()
    assert "2026-10-01" in b["text"] and "Job 03" in b["text"]
    approve_and_send(b)

    hdr = {"X-PP-Bridge-Token": "tok"}
    r1 = c.post("/api/inbound", headers=hdr, json={"id": "msg_in_d1", "provider_message_id": "d1", "raw_text": "yes"}).json()
    assert {a["status"] for a in r1["parsed"]["answers"]} == {"ambiguous"}
    cl = c.post(f"/api/exceptions/{APA['id']}/clarify").json()
    assert sorted(cl["exception_ids"]) == sorted([APA["id"], OFF["id"]])
    approve_and_send(cl)

    r2 = c.post("/api/inbound", headers=hdr, json={"id": "msg_in_d2", "provider_message_id": "d2",
               "raw_text": "The Oct 1 shift was Job 02, the patio build. The disposal run on Job 03 was for the patio job too."}).json()
    assert r2["parsed"]["answers"] and {u["state"] for u in r2["exception_updates"]} == {"needs_approval"}
    res_off = c.get(f"/api/exceptions/{OFF['id']}").json()["resolution"]
    assert res_off["confirmed_facts"] == {"job_id": "job_03", "offsite_parent_job_id": "job_02"}
    res_apa = c.get(f"/api/exceptions/{APA['id']}").json()["resolution"]
    assert res_apa["confirmed_facts"] == {"job_id": "job_02", "time_entry_id": "te_0014"}

    rc = c.post("/api/memory/recall-check", json={
        "query": "Pilot Co disposal cost on job_03 off-site: which job does it belong to?",
        "offsite_child_job_id": "job_03", "next_action": "ask ops lead which job",
        "scope": {"company_label": "Pilot Co", "cycle_id": cid}}).json()
    assert rc["applied"], rc
    assert rc["next_action_before"] == "ask ops lead which job"
    assert rc["next_action_after"] == "propose allocation to job_02 pending owner approval"
    assert rc["approval_created"] is False
