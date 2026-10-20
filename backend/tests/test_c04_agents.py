"""C-04: agents against replies_v1.json. Model calls use a STUB transport (not a live call); the live call is
logged separately in INTEGRATION-FINDINGS. T14/T17 rules are deterministic and run without any model."""
import json
from pathlib import Path

import pytest

from payrollpilot.agents.guard import unauthorized_instruction
from payrollpilot.agents.llm import Budget, BudgetExhausted, OpenRouterLLM
from payrollpilot.agents.resolution import draft_batch, draft_clarification, parse_reply, template_text

FIX = Path(__file__).resolve().parents[2] / "docs/contracts/fixtures"
EXPECTED = json.loads((FIX / "expected_exceptions_v1.json").read_text())["exceptions"]
REPLIES = json.loads((FIX / "replies_v1.json").read_text())["replies"]
BY_CAT = {}
for e in EXPECTED:
    BY_CAT.setdefault(e["category"], e)
JOBS = {"job_01", "job_02", "job_03"}


def resolve(ph: str) -> dict:
    return BY_CAT[ph.strip("{}")]


def case(name):
    r = next(r for r in REPLIES if r["name"] == name)
    excs = [resolve(p) for p in r["batch_exception_ids"]]
    batch = {"id": "msg_batch_t", "exception_ids": [e["id"] for e in excs], "actual_recipient": "+15550000012"}
    inbound = {"id": "msg_in_t", "raw_text": r["raw_text"]}
    return r, excs, batch, inbound


def stub(answers_by_cat):
    """Transport returning a fixed model JSON (shape OpenRouter returns)."""
    def transport(body, headers):
        ids = body["response_format"]["json_schema"]["schema"]["properties"]["answers"]["items"]["properties"]["exception_id"]["enum"]
        ans = []
        for cat, a in answers_by_cat.items():
            ans.append({"exception_id": BY_CAT[cat]["id"], **a})
        assert all(a["exception_id"] in ids for a in ans)
        return {"model": "stub", "usage": {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.0001},
                "choices": [{"message": {"content": json.dumps({"answers": ans})}}]}
    return OpenRouterLLM(transport=transport, budget=Budget(1.0))


def statuses(out):
    return {a["exception_id"]: a["status"] for a in out["parsed"]["answers"]}


def expect_statuses(r):
    return {resolve(k)["id"]: v for k, v in r["expect"]["statuses"].items()}


def test_t14_vague_yes_is_ambiguous_for_all_without_model():
    r, excs, batch, inbound = case("T14 vague yes to three questions")
    out = parse_reply(inbound, batch, excs, JOBS, llm=None)
    assert statuses(out) == expect_statuses(r)
    assert sorted(out["parsed"]["needs_clarification"]) == sorted(resolve(p)["id"] for p in r["expect"]["needs_clarification"])


def test_t17_injection_blocked_before_model():
    r, excs, batch, inbound = case("T17 instruction injection")
    def boom(body, headers):
        raise AssertionError("model must not be called on blocked text")
    out = parse_reply(inbound, batch, excs, JOBS, llm=OpenRouterLLM(transport=boom, budget=Budget(1.0)))
    assert statuses(out) == expect_statuses(r)
    assert out["blocked"] and "payment_instruction" in out["blocked"]
    assert all(not a["extracted"] for a in out["parsed"]["answers"])


def test_clean_answer_with_model():
    r, excs, batch, inbound = case("clean answer")
    llm = stub({"missing_job": {"status": "answered", "job_number": 1, "note": "lawn install", "confidence": 0.95,
                                "quote": "That 2h14 on 9/29 was Job 01"}})
    out = parse_reply(inbound, batch, excs, JOBS, llm=llm)
    assert statuses(out) == expect_statuses(r)
    assert out["parsed"]["answers"][0]["extracted"]["job_id"] == "job_01"


def test_clean_answer_deterministic_fallback_without_key():
    r, excs, batch, inbound = case("clean answer")
    out = parse_reply(inbound, batch, excs, JOBS, llm=OpenRouterLLM(api_key=""))
    assert statuses(out) == expect_statuses(r) and out["parsed"]["model"] == "deterministic_fallback"


def test_partial_with_model_needs_clarification():
    r, excs, batch, inbound = case("partial: answers one of two")
    llm = stub({"duplicate_time": {"status": "answered", "job_number": None, "note": "second entry duplicate", "confidence": 0.9,
                                   "quote": "The second 10/6 entry is a duplicate"},
                "open_timer": {"status": "partial", "job_number": None, "note": "will check", "confidence": 0.8,
                               "quote": "Not sure about the timer"}})
    out = parse_reply(inbound, batch, excs, JOBS, llm=llm)
    assert statuses(out) == expect_statuses(r)
    assert out["parsed"]["needs_clarification"] == [resolve("{open_timer}")["id"]]


def test_model_cannot_answer_with_unknown_job_or_fake_quote():
    r, excs, batch, inbound = case("clean answer")
    llm = stub({"missing_job": {"status": "answered", "job_number": 9, "note": "", "confidence": 0.99, "quote": "Job 09 for sure"}})
    out = parse_reply(inbound, batch, excs, JOBS, llm=llm)
    assert statuses(out)[BY_CAT["missing_job"]["id"]] == "ambiguous"


def test_budget_exhaustion_raises():
    llm = OpenRouterLLM(transport=lambda b, h: {}, budget=Budget(0.0))
    with pytest.raises(BudgetExhausted):
        llm.complete_json("s", "u", "x", {"type": "object"})


def test_draft_includes_dates_and_durations():
    excs = [BY_CAT["missing_job"], BY_CAT["long_shift"]]
    out = draft_batch(excs, llm=None)
    assert out["wording"] == "template"
    assert "2026-09-29" in out["text"] and "2h14m" in out["text"] and "1)" in out["text"] and "2)" in out["text"]
    assert "+1" not in out["text"]


def test_clarification_stays_in_scope():
    batch = {"id": "b1", "exception_ids": [BY_CAT["open_timer"]["id"]], "actual_recipient": "+15550000012"}
    c = draft_clarification(batch, [BY_CAT["open_timer"]["id"], BY_CAT["missing_job"]["id"]], EXPECTED)
    assert c["exception_ids"] == [BY_CAT["open_timer"]["id"]] and c["actual_recipient"] == batch["actual_recipient"]
    with pytest.raises(ValueError):
        draft_clarification(batch, [BY_CAT["missing_job"]["id"]], EXPECTED)


def test_guard_does_not_flag_normal_answers():
    for r in REPLIES:
        if "T17" not in r["name"]:
            assert unauthorized_instruction(r["raw_text"]) == [], r["name"]
