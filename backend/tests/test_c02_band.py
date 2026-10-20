"""C-02 unit tests: band CLI wrapper (subprocess mocked), decision parsing, handoff orchestration, delete test."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from payrollpilot.band import BandRequired, CliBand, NullBand, case_card, get_band, handoff_to_resolution, parse_decision

EXC = {"id": "exc_0001", "category": "missing_job", "title": "Shift on 10/02 has no job assigned",
       "stage_impact": {"stage1_wages": "none", "stage2_costs": "job_costing"},
       "intended_respondent_role": "ops_lead", "provenance": "seeded_issue"}


class Recorder:
    def __init__(self, outputs):
        self.calls, self.outputs = [], list(outputs)

    def __call__(self, args, **kw):
        self.calls.append(args)
        return SimpleNamespace(returncode=0, stdout=self.outputs.pop(0) if self.outputs else "", stderr="")


def test_cli_send_uses_body_file_and_session():
    rec = Recorder(["sent abc-123"])
    band = CliBand(room_id="room1", bin_path="band", runner=rec)
    assert band.post("pp-audit", "hello") == "abc-123"
    args = rec.calls[0]
    assert args[:3] == ["band", "send", "room1"] and "--body-file" in args and args[-2:] == ["--session", "pp-audit"]


def test_cli_assign_returns_uid():
    band = CliBand(room_id="room1", bin_path="band", runner=Recorder(["#4 exc_0001 missing_job"]))
    assert band.assign("pp-audit", "exc_0001 missing_job") == "#4"


def test_cli_error_raises():
    def failing(args, **kw):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")
    with pytest.raises(Exception, match="boom"):
        CliBand(room_id="r", bin_path="band", runner=failing).board()


def test_null_band_refuses_every_call(monkeypatch):
    monkeypatch.setenv("PP_BAND_ENABLED", "0")
    band = get_band()
    assert isinstance(band, NullBand)
    with pytest.raises(BandRequired):
        handoff_to_resolution(band, EXC)


def test_decision_only_from_human_naming_exact_target():
    human = {"sender_type": "User", "content": "@[[x]] approve msg_batch_01"}
    assert parse_decision(human, "msg_batch_01") == "approve"
    assert parse_decision({**human, "sender_type": "Agent"}, "msg_batch_01") is None
    assert parse_decision(human, "msg_batch_02") is None
    assert parse_decision({"sender_type": "User", "content": "approve msg_batch_01 reject msg_batch_01"}, "msg_batch_01") is None
    assert parse_decision({"sender_type": "User", "content": "Reject msg_batch_01 please"}, "msg_batch_01") == "reject"


def test_case_card_is_minimized():
    card = case_card(EXC)
    assert "exc_0001" in card and "missing_job" in card and "seeded_issue" in card
    assert "$" not in card and "+1" not in card


class FakeBand:
    def __init__(self):
        self.log, self.queue = [], {}

    def post(self, agent, text):
        mid = f"m{len(self.log)}"
        self.log.append(("post", agent, text))
        self.queue.setdefault("pp-resolution", []).append({"message_id": mid, "content": text, "sender_type": "Agent"})
        return mid

    def inbox(self, agent):
        return self.queue.get(agent, [])

    def reply(self, agent, mid, text):
        self.log.append(("reply", agent, mid)); return "r1"

    def assign(self, agent, subject, detail=""):
        self.log.append(("assign", agent, subject)); return "#1"

    def take(self, agent, uid):
        self.log.append(("take", agent, uid))

    def set_status(self, agent, uid, status):
        self.log.append(("status", agent, uid, status))


def test_handoff_sequence():
    fb = FakeBand()
    out = handoff_to_resolution(fb, EXC, sleep=0)
    assert out["accepted"] and out["task_uid"] == "#1"
    kinds = [(e[0], e[1]) for e in fb.log]
    assert kinds == [("post", "pp-audit"), ("assign", "pp-audit"), ("reply", "pp-resolution"),
                     ("take", "pp-resolution"), ("status", "pp-resolution")]


@pytest.mark.parametrize("failure", [OSError("test unavailable"), __import__("subprocess").TimeoutExpired("band", 1)])
def test_cli_unreachable_and_timeout_are_explicit_band_failures(failure):
    from payrollpilot.band import BandError
    def unavailable(*args, **kwargs):
        raise failure
    with pytest.raises(BandError):
        CliBand(room_id="room_test", bin_path="band", runner=unavailable).inbox("pp-resolution")
