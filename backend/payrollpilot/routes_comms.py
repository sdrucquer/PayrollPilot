"""Lane C routes (CONTRACTS section 5): handoff, messages draft/send, inbound, clarify, memory recall-check,
plus the Band owner-decision check. Thin: permissions.py and coordinator.py decide; agents propose."""
from __future__ import annotations

import asyncio
import hmac
import os
import threading
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import approvals, kinds
from .agents.audit import investigation_note, propose_respondent
from .agents.llm import BudgetExhausted, OpenRouterLLM
from .agents.resolution import draft_batch, draft_clarification, parse_reply
from .band import BandError, BandRequired, CliBand, NullBand, handoff_to_resolution, request_owner_decision, deliver_to_payroll
from .coordinator import TransitionRejected, is_stopped, transition
from .db import now_iso
from .events import emit, new_id
from .memory.apply import ASK_AGAIN, apply_recall
from .memory.base import InMemoryMemory
from .permissions import PermissionDenied, batch_version, check_recipient, check_send, text_hash
from .settings import mask_handle

router = APIRouter()
_lock = threading.Lock()
_batch_action_lock = threading.Lock()


# ---------------------------------------------------------------- adapters
def _comms(request: Request) -> dict:
    st = request.app.state
    with _lock:
        if not hasattr(st, "pp_comms"):
            s = st.pp.settings
            if s.memory_mode == "cognee":
                from .memory.cognee_memory import CogneeMemory
                memory = CogneeMemory()
            else:
                memory = InMemoryMemory()
            band = CliBand() if s.band_mode == "cli" else NullBand()
            st.pp_comms = {
                "memory": memory, "band": band,
                "llm": OpenRouterLLM(), "llm_cheap": OpenRouterLLM(model=os.environ.get("PP_MODEL_CHEAP", "anthropic/claude-haiku-5.5")),
                "band_tasks": {},
            }
    return st.pp_comms


def _err(status: int, code: str, detail: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "detail": detail, **extra})


def _strip(r: dict | None) -> dict | None:
    return {k: v for k, v in r.items() if k != "_version"} if r else None


def _stopped(db) -> JSONResponse | None:
    return _err(409, "run_stopped", "run is stopped; no new actions") if is_stopped(db) else None


def _advance(db, exc_id: str, target: str, actor: str, reason: str, next_action: str | None = None) -> dict | None:
    """Walk the forward chain to ``target`` one legal step at a time (coordinator validates each)."""
    chain = ["detected", "investigating", "awaiting_reply", "answer_received", "needs_approval"]
    exc = db.get_record(kinds.EXCEPTION, exc_id)
    if exc is None or exc["state"] == target:
        return exc
    if exc["state"] in chain and target in chain:
        for nxt in chain[chain.index(exc["state"]) + 1: chain.index(target) + 1]:
            exc = transition(db, exc_id, nxt, actor, reason=reason, next_action=next_action if nxt == target else None)
        return exc
    return transition(db, exc_id, target, actor, reason=reason, next_action=next_action)


def _update(db, kind: str, rec: dict, **changes) -> dict:
    new = {k: v for k, v in rec.items() if k != "_version"}
    new.update(changes)
    return db.put_record(kind, new)


def _job_names(db, cycle_id: str | None) -> dict[str, str]:
    from .cycles import get_snapshot
    snap = (get_snapshot(db, cycle_id) if cycle_id else None) or {}
    return {j["id"]: j.get("display_name") or j["id"] for j in snap.get("jobs") or []}


def _known_ids(db, cycle_id: str | None) -> dict[str, set[str]]:
    from .cycles import get_snapshot
    snap = get_snapshot(db, cycle_id) if cycle_id else None
    snap = snap or {}
    return {
        "job_ids": {j["id"] for j in snap.get("jobs") or []},
        "time_entry_ids": {t["id"] for t in snap.get("time_entries") or []},
        "resolution_ids": {r["id"] for r in db.list_records(kinds.RESOLUTION)},
    }



# ---------------------------------------------------------------- handoff
@router.post("/api/exceptions/{exception_id}/handoff")
def handoff(exception_id: str, request: Request):
    st = request.app.state.pp
    if (r := _stopped(st.db)):
        return r
    exc = st.db.get_record(kinds.EXCEPTION, exception_id)
    if exc is None:
        return _err(404, "not_found", f"exception {exception_id} not found")
    band = _comms(request)["band"]
    if not band.enabled:
        return _err(503, "band_required", "Band is disabled (PP_BAND_ENABLED=0); the case cannot move to Resolution")
    if exc.get("owner_agent") not in (None, "audit"):
        return _err(409, "already_handed_off", f"case owner is {exc.get('owner_agent')}")
    emit(st.db, type="handoff.requested", actor="audit", cycle_id=exc.get("cycle_id"),
         summary=f"Audit -> Resolution: {exception_id} ({investigation_note(exc)})",
         refs={"exception_id": exception_id, "respondent": propose_respondent(exc)})
    try:
        out = handoff_to_resolution(band, _strip(exc))
    except (BandError, BandRequired) as e:
        return _err(502, "band_error", str(e))
    if not out.get("accepted"):
        return _err(504, "band_not_delivered", "Resolution peer did not receive the card", band=out)
    _comms(request)["band_tasks"][exception_id] = out.get("task_uid")
    if exc["state"] == "detected":
        exc = transition(st.db, exception_id, "investigating", "resolution", reason="handoff accepted",
                         next_action=f"draft question for {propose_respondent(exc)}")
    exc = _update(st.db, kinds.EXCEPTION, st.db.get_record(kinds.EXCEPTION, exception_id), owner_agent="resolution",
                  band_handoff={**out, "room_id": band.room_id}, updated_at=now_iso())
    ev = emit(st.db, type="handoff.accepted", actor="resolution", cycle_id=exc.get("cycle_id"),
              summary=f"Resolution accepted {exception_id} in Band", refs={"exception_id": exception_id, "band": out})
    return {"event": ev, "exception": _strip(exc), "band": out}


def _coordinate_new_cases(request: Request, excs: list[dict]):
    """Home can start at Draft: acquire the same real Band handoff first.

    New case ownership is persisted only after room delivery, acknowledgement,
    task claim and in-progress update succeed. Restart does not erase that proof.
    """
    st = request.app.state.pp
    band = _comms(request)["band"]
    if not band.enabled:
        return _err(503, "band_required", "Band is required before drafting new workflow messages")
    for exc in excs:
        proof = exc.get("band_handoff") or {}
        if proof.get("accepted") and proof.get("task_uid") and proof.get("room_id") == band.room_id:
            continue
        emit(st.db, type="handoff.requested", actor="audit", cycle_id=exc.get("cycle_id"),
             summary=f"Audit requests Band handoff for {exc['id']} before drafting",
             refs={"exception_id": exc["id"], "room_id": band.room_id})
        try:
            out = handoff_to_resolution(band, _strip(exc))
        except (BandError, BandRequired) as e:
            return _err(502, "band_error", str(e))
        if not out.get("accepted"):
            return _err(504, "band_not_delivered", "Resolution did not accept the case in Band")
        if exc["state"] == "detected":
            transition(st.db, exc["id"], "investigating", "resolution", reason="Band handoff accepted before draft",
                       next_action="draft question for owner review")
        _update(st.db, kinds.EXCEPTION, st.db.get_record(kinds.EXCEPTION, exc["id"]), owner_agent="resolution",
                band_handoff={**out, "room_id": band.room_id}, updated_at=now_iso())
        emit(st.db, type="handoff.accepted", actor="resolution", cycle_id=exc.get("cycle_id"),
             summary=f"Resolution accepted {exc['id']} in Band before drafting",
             refs={"exception_id": exc["id"], "band": out, "room_id": band.room_id})
    return None


def _publish_new_batch(request: Request, batch: dict):
    """No persisted/sendable draft when Band cannot publish its owner decision."""
    st = request.app.state.pp
    band = _comms(request)["band"]
    if not band.enabled:
        return _err(503, "band_required", "Band is required for new workflow drafts")
    try:
        mid = request_owner_decision(band, batch["id"], batch["text_hash"],
                                     f"review {len(batch['exception_ids'])} question(s); send only after owner approval")
    except (BandError, BandRequired) as e:
        return _err(502, "band_error", str(e))
    if not mid:
        return _err(502, "band_error", "Band did not return an owner-decision message id")
    batch.update(band_coordination_required=True, band_decision_message_id=mid, band_room_id=band.room_id,
                 band_decision_version=batch["text_hash"])
    return None


@router.post("/api/corrections/{correction_id}/payroll-handoff")
def payroll_handoff(correction_id: str, request: Request):
    """Accept an already owner-applied result in Band; never applies a correction."""
    st = request.app.state.pp
    with _batch_action_lock:
        corr = st.db.get_record(kinds.CORRECTION, correction_id)
        if corr is None:
            return _err(404, "not_found", "correction not found")
        if corr.get("state") != "applied" or not corr.get("approval_id"):
            return _err(409, "correction_not_applied", "Owner approval and local application must happen first")
        proof = corr.get("band_payroll_handoff") or {}
        if proof.get("received") and proof.get("reply_message_id"):
            return {"received": True, "duplicate": True, "band": proof}
        if (r := _stopped(st.db)):
            return r
        band = _comms(request)["band"]
        if not band.enabled:
            return _err(503, "band_required", "Payroll handoff requires Band")
        res = st.db.get_record(kinds.RESOLUTION, corr.get("resolution_id")) if corr.get("resolution_id") else None
        exc = st.db.get_record(kinds.EXCEPTION, res["exception_id"]) if res else None
        if exc is None:
            matches = [e for e in st.db.list_records(kinds.EXCEPTION, cycle_id=corr.get("cycle_id"))
                       if e.get("resolved_by_correction_id") == correction_id]
            exc = matches[0] if len(matches) == 1 else None
        if exc is None:
            return _err(409, "handoff_case_unknown", "Applied correction needs its evidenced case before a payroll handoff")
        task = (exc.get("band_handoff") or {}).get("task_uid")
        if not task:
            for event in st.db.list_events(cycle_id=corr["cycle_id"], limit=5000):
                refs = event.get("refs") or {}
                if event["type"] == "handoff.accepted" and refs.get("exception_id") == exc["id"]:
                    task = (refs.get("band") or {}).get("task_uid") or task
        try:
            out = deliver_to_payroll(band, exc, corr, task)
        except (BandError, BandRequired) as e:
            return _err(502, "band_error", str(e))
        if not out.get("received") or not out.get("reply_message_id"):
            return _err(504, "payroll_not_delivered", "Payroll did not accept the applied correction in Band")
        proof = {**out, "room_id": band.room_id, "task_uid": task}
        _update(st.db, kinds.CORRECTION, corr, band_payroll_handoff=proof)
        emit(st.db, type="handoff.accepted", actor="payroll", cycle_id=corr["cycle_id"],
             summary=f"Payroll accepted owner-applied correction {correction_id} in Band",
             refs={"correction_id": correction_id, "exception_id": exc["id"], "band": proof})
        return {"received": True, "duplicate": False, "band": proof}


# ---------------------------------------------------------------- draft
class DraftRequest(BaseModel):
    exception_ids: list[str]


@router.post("/api/messages/draft")
def draft(body: DraftRequest, request: Request):
    with _batch_action_lock:
        return _draft_locked(body, request)


def _draft_locked(body: DraftRequest, request: Request):
    st = request.app.state.pp
    if (r := _stopped(st.db)):
        return r
    excs = [st.db.get_record(kinds.EXCEPTION, i) for i in body.exception_ids]
    if not excs or any(e is None for e in excs):
        return _err(404, "not_found", "unknown exception id")
    cycles_ = {e["cycle_id"] for e in excs}
    roles = {propose_respondent(e) for e in excs}
    if len(cycles_) != 1 or len(roles) != 1:
        return _err(422, "mixed_batch", "a batch covers one cycle and one intended respondent")
    recipient = check_recipient(st.settings.test_recipient, st.settings.allowlist)  # 403 if not configured
    c = _comms(request)
    if (error := _coordinate_new_cases(request, excs)) is not None:
        return error
    try:
        d = draft_batch([_strip(e) for e in excs], c["llm"], st.settings.company_label)
    except BudgetExhausted as e:
        emit(st.db, type="budget.exhausted", actor="system", cycle_id=cycles_.pop(), summary=str(e))
        return _err(429, "budget_exhausted", str(e))
    batch = {
        "id": new_id("msg_batch"), "cycle_id": excs[0]["cycle_id"], "exception_ids": body.exception_ids,
        "intended_respondent_role": roles.pop(), "intended_respondent_label": st.settings.intended_respondent_label,
        "actual_recipient": recipient, "channel": "imessage", "text": d["text"], "text_hash": text_hash(d["text"]),
        "approval_id": None, "state": "draft", "provider_message_id": None, "sent_at": None, "provider_status": None,
        "provenance": "real", "wording": d["wording"], "parent_batch_id": None, "created_at": now_iso(),
    }
    if (error := _publish_new_batch(request, batch)) is not None:
        return error
    st.db.put_record(kinds.MESSAGE_BATCH, batch)
    emit(st.db, type="message.drafted", actor="resolution", cycle_id=batch["cycle_id"],
         summary=f"Drafted {len(excs)} question(s) for {batch['intended_respondent_label']} -> {mask_handle(recipient)}",
         refs={"batch_id": batch["id"], "exception_ids": body.exception_ids, "wording": d["wording"]}, usage=d["usage"])
    return _public_batch(batch)


def _public_batch(b: dict) -> dict:
    out = _strip(dict(b))
    out["actual_recipient_masked"] = mask_handle(b["actual_recipient"])
    out["target_version"] = batch_version(b)  # what POST /api/approvals must bind to
    out.pop("actual_recipient", None)
    return out


# Owner edits/declines append new versions; neither action sends a message.
class DraftVersionRequest(BaseModel):
    target_version: str


class EditDraftRequest(DraftVersionRequest):
    text: str


def _editable_batch(st, batch_id: str, version: str):
    batch = st.db.get_record(kinds.MESSAGE_BATCH, batch_id)
    if batch is None:
        return None, _err(404, "not_found", "message batch not found")
    send_state = st.db.send_state(batch_id)
    if batch.get("declined_at") or batch.get("state") not in {"draft", "approved"} or (send_state and send_state["state"] in {"sending", "sent"}):
        return None, _err(409, "batch_not_editable", "only an unsent, non-declined draft can change")
    if version != batch_version(batch):
        return None, _err(409, "stale_version", "draft changed; review its current text first")
    return batch, None


@router.post("/api/messages/{batch_id}/edit")
def edit_draft(batch_id: str, body: EditDraftRequest, request: Request):
    st = request.app.state.pp
    with _batch_action_lock:
        if (r := _stopped(st.db)):
            return r
        if not body.text.strip() or len(body.text) > 10000:
            return _err(422, "invalid_text", "message text must contain 1 to 10000 characters")
        batch, error = _editable_batch(st, batch_id, body.target_version)
        if error is not None:
            return error
        if body.text == batch["text"]:
            return _public_batch(batch)
        approvals.invalidate_for_target(st.db, batch_id, "owner edited message text", batch["cycle_id"])
        updated = _update(st.db, kinds.MESSAGE_BATCH, batch, text=body.text, text_hash=text_hash(body.text),
                          approval_id=None, state="draft")
        emit(st.db, type="message.drafted", actor="owner", cycle_id=batch["cycle_id"],
             summary="Owner edited the message; new approval required", refs={"batch_id": batch_id, "edited": True})
        return _public_batch(updated)


@router.post("/api/messages/{batch_id}/decline")
def decline_draft(batch_id: str, body: DraftVersionRequest, request: Request):
    st = request.app.state.pp
    with _batch_action_lock:
        batch, error = _editable_batch(st, batch_id, body.target_version)
        if error is not None:
            return error
        approvals.invalidate_for_target(st.db, batch_id, "owner declined message", batch["cycle_id"])
        updated = _update(st.db, kinds.MESSAGE_BATCH, batch, declined_at=now_iso(), approval_id=None, state="draft")
        emit(st.db, type="approval.invalidated", actor="owner", cycle_id=batch["cycle_id"],
             summary="Owner declined the message; nothing sent", refs={"batch_id": batch_id, "decision": "declined"})
        return _public_batch(updated)


# ---------------------------------------------------------------- band decision -> approval
@router.post("/api/messages/{batch_id}/band-decision")
def band_decision(batch_id: str, request: Request):
    """Read the owner's reply in the Band room. An 'approve <batch_id>' from a human becomes an Approval
    through the normal approvals path (same version check as the UI button). Band itself grants nothing."""
    st = request.app.state.pp
    batch = st.db.get_record(kinds.MESSAGE_BATCH, batch_id)
    if batch is None:
        return _err(404, "not_found", f"batch {batch_id} not found")
    band = _comms(request)["band"]
    if not band.enabled:
        return _err(503, "band_required", "Band is disabled")
    if batch.get("band_coordination_required") and batch.get("band_decision_version") != batch_version(batch):
        return _err(409, "band_decision_stale", "Text changed after the Band request; review in the UI or create a fresh draft")
    found = band.find_decision("pp-resolution", batch_id)
    if not found:
        return {"decision": None}
    if found["decision"] == "reject":
        return {"decision": "reject", "band": found}
    try:
        appr = approvals.create_approval(
            st.db, kind="message_send", target_id=batch_id, target_version=batch_version(batch),
            scope_text=f"Owner approved in Band room (message {found['band_message_id']}): send this exact text to the allowlisted test recipient")
    except approvals.ApprovalError as e:
        return _err(e.status, e.code, e.detail, **e.extra)
    return {"decision": "approve", "approval": appr, "band": found}


# ---------------------------------------------------------------- send
@router.post("/api/messages/{batch_id}/send")
def send(batch_id: str, request: Request):
    with _batch_action_lock:
        return _send_locked(batch_id, request)


def _send_locked(batch_id: str, request: Request):
    st = request.app.state.pp
    if (r := _stopped(st.db)):
        return r
    batch = st.db.get_record(kinds.MESSAGE_BATCH, batch_id)
    if batch is None:
        return _err(404, "not_found", f"batch {batch_id} not found")
    if batch.get("declined_at"):
        return _err(409, "batch_declined", "owner declined this message; nothing sent")
    prior = st.db.send_state(batch_id)
    if prior and prior["state"] in ("sent", "sending"):
        return {**_public_batch(batch), "duplicate": True, "send_state": prior}
    # Existing approved runtime cases retain their original gates. New coordinated
    # batches additionally require a reachable Band room before any provider effect.
    if batch.get("band_coordination_required"):
        band = _comms(request)["band"]
        if not band.enabled:
            return _err(503, "band_required", "Band is required for this coordinated workflow")
        if not batch.get("band_decision_message_id") or batch.get("band_room_id") != band.room_id:
            return _err(409, "band_coordination_missing", "Review this workflow in its Band room before sending")
        try:
            band.inbox("pp-resolution")
        except (BandError, BandRequired) as e:
            return _err(502, "band_error", str(e))
    appr = approvals.require_active_approval(st.db, batch.get("approval_id"))
    check_send(batch, appr, st.settings.allowlist)  # PermissionDenied -> 403
    if batch["text_hash"] != text_hash(batch["text"]):
        raise PermissionDenied("batch.hash_mismatch", "text changed after drafting")
    if not st.db.claim_send(batch_id):
        return {**_public_batch(batch), "duplicate": True, "send_state": st.db.send_state(batch_id)}
    messaging = st.messaging
    try:
        res = messaging.send(batch)
    except Exception as e:  # provider/bridge failure: record, never pretend
        st.db.record_send_result(batch_id, None, "failed")
        batch = _update(st.db, kinds.MESSAGE_BATCH, batch, state="failed", provider_status=str(e)[:200])
        return _err(502, "send_failed", str(e)[:300], batch=_public_batch(batch))
    pmid = res.get("provider_message_id")
    st.db.record_send_result(batch_id, pmid, "sent")
    fake = getattr(messaging, "mode", "") == "fake"
    batch = _update(st.db, kinds.MESSAGE_BATCH, batch, state="sent", provider_message_id=pmid, sent_at=now_iso(),
                    provider_status=res.get("status"), provenance="synthetic" if fake else "real",
                    provider_space_id=res.get("provider_space_id"))
    for exc_id in batch["exception_ids"]:
        try:
            _advance(st.db, exc_id, "awaiting_reply", "resolution", f"question sent in {batch_id}", next_action="wait for reply")
        except TransitionRejected:
            pass
    emit(st.db, type="message.sent", actor="resolution", cycle_id=batch["cycle_id"],
         summary=("FAKE (dev only) " if fake else "") + f"Sent {batch_id} to {mask_handle(batch['actual_recipient'])}",
         refs={"batch_id": batch_id, "provider_message_id": pmid, "messaging_mode": getattr(messaging, "mode", "?")})
    return _public_batch(batch)


# ---------------------------------------------------------------- inbound
def _correlate(db, inbound: dict) -> dict | None:
    if inbound.get("correlated_batch_id"):
        return db.get_record(kinds.MESSAGE_BATCH, inbound["correlated_batch_id"])
    sent = [b for b in db.list_records(kinds.MESSAGE_BATCH) if b.get("state") == "sent"]
    open_ = [b for b in sent if any((db.get_record(kinds.EXCEPTION, e) or {}).get("state") == "awaiting_reply" for e in b["exception_ids"])]
    pool = open_ or sent
    return max(pool, key=lambda b: b.get("sent_at") or "") if pool else None


def _write_memory_bg(memory, db, res: dict) -> None:
    try:
        ref = asyncio.run(memory.write_resolution(res))
        rec = db.get_record(kinds.RESOLUTION, res["id"])
        if rec:
            _update(db, kinds.RESOLUTION, rec, memory_ref=ref)
        emit(db, type="memory.written", actor="resolution", cycle_id=res["cycle_id"],
             summary=f"{getattr(memory, 'name', '?')}: stored {res['id']}", refs={"resolution_id": res["id"], "memory_ref": ref})
    except Exception as e:  # noqa: BLE001
        emit(db, type="memory.written", actor="system", cycle_id=res["cycle_id"],
             summary=f"memory write FAILED for {res['id']}: {str(e)[:150]}", refs={"resolution_id": res["id"], "failed": True})


@router.post("/api/inbound")
def inbound(body: dict, request: Request, background: BackgroundTasks,
            x_pp_bridge_token: Optional[str] = Header(default=None)):
    st = request.app.state.pp
    if not x_pp_bridge_token or not hmac.compare_digest(x_pp_bridge_token, st.settings.bridge_token):
        return _err(401, "bad_bridge_token", "inbound requires the bridge token")
    pmid = body.get("provider_message_id")
    if not pmid or not isinstance(body.get("raw_text"), str):
        return _err(422, "bad_inbound", "provider_message_id and raw_text required")
    inbound_id = body.get("id") or new_id("msg_in")
    if not st.db.claim_inbound(pmid, inbound_id):
        return {"duplicate": True, "provider_message_id": pmid}
    batch = _correlate(st.db, body)
    rec = {**body, "id": inbound_id, "dedupe_key": pmid, "correlated_batch_id": batch["id"] if batch else None,
           "respondent_intended_role": batch.get("intended_respondent_role") if batch else None,
           "provenance": body.get("provenance", "test_reply"), "received_at": body.get("received_at") or now_iso()}
    st.db.put_record(kinds.INBOUND, rec)
    cycle_id = batch["cycle_id"] if batch else None
    emit(st.db, type="message.received", actor="bridge", cycle_id=cycle_id,
         summary=f"Reply {inbound_id} ({len(rec['raw_text'])} chars) -> {rec['correlated_batch_id'] or 'uncorrelated'}",
         refs={"inbound_id": inbound_id, "provider_message_id": pmid, "batch_id": rec["correlated_batch_id"]})
    if batch is None:
        return {"duplicate": False, "inbound_id": inbound_id, "parsed": None, "exception_updates": [], "note": "no sent batch to correlate"}

    c = _comms(request)
    excs = [_strip(st.db.get_record(kinds.EXCEPTION, i)) for i in batch["exception_ids"]]
    excs = [e for e in excs if e]
    known = _known_ids(st.db, cycle_id)
    try:
        out = parse_reply(rec, batch, excs, known["job_ids"], c["llm_cheap"], _job_names(st.db, cycle_id))
    except BudgetExhausted as e:
        emit(st.db, type="budget.exhausted", actor="system", cycle_id=cycle_id, summary=str(e))
        return _err(429, "budget_exhausted", str(e))
    parsed = out["parsed"]
    st.db.put_record(kinds.PARSED_REPLY, {"id": inbound_id, **parsed})
    emit(st.db, type="reply.parsed", actor="resolution", cycle_id=cycle_id,
         summary=f"Parsed {inbound_id}: " + ", ".join(f"{a['exception_id']}={a['status']}" for a in parsed["answers"]),
         refs={"inbound_id": inbound_id, "model": parsed.get("model")}, usage=out.get("usage"))

    updates: list[dict] = []
    if out["blocked"]:
        emit(st.db, type="blocked.unauthorized_instruction", actor="resolution", cycle_id=cycle_id,
             summary=f"Reply {inbound_id} contained instructions ({', '.join(out['blocked'])}); treated as data, no action taken",
             refs={"inbound_id": inbound_id, "codes": out["blocked"]})
        return {"duplicate": False, "inbound_id": inbound_id, "parsed": parsed, "blocked": out["blocked"], "exception_updates": []}

    for a in parsed["answers"]:
        exc = next((e for e in excs if e["id"] == a["exception_id"]), None)
        if exc is None:
            continue
        try:
            if a["status"] == "answered":
                _advance(st.db, exc["id"], "answer_received", "resolution", f"answered in {inbound_id}")
                facts = dict(a.get("extracted") or {})
                facts.pop("note", None)
                refs_ = exc.get("entity_refs") or {}
                te = refs_.get("time_entry_ids") or []
                if exc.get("category") == "offsite_link" and facts.get("job_id") and refs_.get("job_ids"):
                    # Reply names the parent; the exception's job is the off-site child.
                    facts = {"job_id": refs_["job_ids"][0], "offsite_parent_job_id": facts["job_id"]}
                elif te:
                    facts.setdefault("time_entry_id", te[0])
                res = {
                    "id": new_id("res"), "exception_id": exc["id"], "cycle_id": exc["cycle_id"], "confirmed_facts": facts,
                    "evidence": exc.get("evidence") or [], "inbound_ids": [inbound_id], "confirmer_actual": "owner_test_phone",
                    "confirmer_intended_role": batch.get("intended_respondent_role"),
                    "scope": {"company_label": st.settings.company_label, "cycle_id": exc["cycle_id"],
                              "job_ids": [facts["job_id"]] if facts.get("job_id") else [],
                              "worker_ids": [w for w in [(exc.get("entity_refs") or {}).get("worker_id")] if w]},
                    "approved_correction_id": None, "created_at": now_iso(), "memory_ref": None, "provenance": "test_reply",
                }
                st.db.put_record(kinds.RESOLUTION, res)
                emit(st.db, type="resolution.recorded", actor="resolution", cycle_id=exc["cycle_id"],
                     summary=f"{exc['id']}: {facts}", refs={"resolution_id": res["id"], "exception_id": exc["id"]})
                new = _advance(st.db, exc["id"], "needs_approval", "resolution", "resolution recorded",
                               next_action="propose correction for owner approval")
                _update(st.db, kinds.EXCEPTION, st.db.get_record(kinds.EXCEPTION, exc["id"]), resolution_id=res["id"])
                background.add_task(_write_memory_bg, c["memory"], st.db, res)
                updates.append({"exception_id": exc["id"], "state": new["state"], "resolution_id": res["id"]})
            elif a["status"] == "conflicting":
                new = transition(st.db, exc["id"], "conflicting", "resolution", reason=f"conflicting reply {inbound_id}",
                                 next_action="escalate to owner: reply conflicts")
                updates.append({"exception_id": exc["id"], "state": new["state"]})
            elif a["status"] in ("partial", "ambiguous"):
                emit(st.db, type="clarification.needed", actor="resolution", cycle_id=exc["cycle_id"],
                     summary=f"{exc['id']}: {a['status']} reply; clarification needed", refs={"exception_id": exc["id"], "inbound_id": inbound_id})
                updates.append({"exception_id": exc["id"], "state": exc["state"], "needs_clarification": True})
        except TransitionRejected as e:
            updates.append({"exception_id": exc["id"], "state": exc["state"], "rejected": str(e)})
    return {"duplicate": False, "inbound_id": inbound_id, "parsed": parsed, "blocked": [], "exception_updates": updates}


# ---------------------------------------------------------------- clarify
@router.post("/api/exceptions/{exception_id}/clarify")
def clarify(exception_id: str, request: Request):
    with _batch_action_lock:
        return _clarify_locked(exception_id, request)


def _clarify_locked(exception_id: str, request: Request):
    st = request.app.state.pp
    if (r := _stopped(st.db)):
        return r
    exc = st.db.get_record(kinds.EXCEPTION, exception_id)
    if exc is None:
        return _err(404, "not_found", f"exception {exception_id} not found")
    batches = [b for b in st.db.list_records(kinds.MESSAGE_BATCH) if exception_id in b["exception_ids"] and b.get("state") == "sent"]
    if not batches:
        return _err(409, "no_sent_batch", "nothing was asked yet; draft a batch instead")
    parent = max(batches, key=lambda b: b.get("sent_at") or "")
    check_recipient(parent["actual_recipient"], st.settings.allowlist)
    # Cover every question in the parent batch that is still open, not only this one.
    open_ = [_strip(st.db.get_record(kinds.EXCEPTION, i)) for i in parent["exception_ids"]]
    open_ = [e for e in open_ if e and e["state"] == "awaiting_reply"] or [_strip(exc)]
    if (error := _coordinate_new_cases(request, open_)) is not None:
        return error
    cl = draft_clarification(parent, [e["id"] for e in open_], open_, st.settings.company_label)
    batch = {**{k: v for k, v in parent.items() if k != "_version"}, "id": new_id("msg_batch"), "exception_ids": cl["exception_ids"],
             "text": cl["text"], "text_hash": text_hash(cl["text"]), "approval_id": None, "state": "draft",
             "provider_message_id": None, "sent_at": None, "provider_status": None, "parent_batch_id": parent["id"],
             "wording": "template", "created_at": now_iso()}
    if (error := _publish_new_batch(request, batch)) is not None:
        return error
    st.db.put_record(kinds.MESSAGE_BATCH, batch)
    emit(st.db, type="message.drafted", actor="resolution", cycle_id=batch["cycle_id"],
         summary=f"Clarification for {exception_id} (follow-up to {parent['id']}); needs new approval",
         refs={"batch_id": batch["id"], "parent_batch_id": parent["id"], "exception_ids": cl["exception_ids"]})
    return _public_batch(batch)


# ---------------------------------------------------------------- memory recall-check (T15)
class RecallCheck(BaseModel):
    query: str
    scope: dict[str, Any] = {}
    exception_id: Optional[str] = None
    parent_job_id: Optional[str] = None
    offsite_child_job_id: Optional[str] = None
    next_action: Optional[str] = None


@router.post("/api/memory/recall-check")
def recall_check(body: RecallCheck, request: Request):
    st = request.app.state.pp
    c = _comms(request)
    memory = c["memory"]
    exc = st.db.get_record(kinds.EXCEPTION, body.exception_id) if body.exception_id else None
    cycle_id = (exc or {}).get("cycle_id") or body.scope.get("cycle_id")
    case = {"exception_id": body.exception_id, "cycle_id": cycle_id,
            "company_label": body.scope.get("company_label", st.settings.company_label),
            "parent_job_id": body.parent_job_id, "offsite_child_job_id": body.offsite_child_job_id, "next_action": body.next_action or (exc or {}).get("next_action") or ASK_AGAIN}
    hits = asyncio.run(memory.recall(body.query, body.scope))
    emit(st.db, type="memory.recalled", actor="payroll", cycle_id=cycle_id,
         summary=f"{getattr(memory, 'name', '?')}: {len(hits)} hit(s) for '{body.query[:80]}'",
         refs={"exception_id": body.exception_id, "hit_count": len(hits), "memory_adapter": getattr(memory, "name", "?")})
    known = _known_ids(st.db, cycle_id)
    if body.scope.get("known_ids"):  # demo/T15 harness may pass ids when no snapshot is loaded
        for k, v in body.scope["known_ids"].items():
            known.setdefault(k, set()).update(v)
    out = apply_recall(case, hits, known)
    if out["applied"]:
        emit(st.db, type="memory.applied", actor="payroll", cycle_id=cycle_id,
             summary=f"Recall changed next action: '{out['next_action_before']}' -> '{out['next_action_after']}'",
             refs={"exception_id": body.exception_id, "proposed": out.get("proposed")})
        if exc is not None:
            _update(st.db, kinds.EXCEPTION, exc, next_action=out["next_action_after"], updated_at=now_iso())
    return {"hits": [{"text": h.text, "refs": h.refs, "source": h.source} for h in hits], "applied": out["applied"],
            "next_action_before": out["next_action_before"], "next_action_after": out["next_action_after"],
            "memory_adapter": getattr(memory, "name", "?"), "approval_created": False, "rejected": out.get("rejected", [])}


@router.get("/api/comms/health")
def comms_health(request: Request):
    c = _comms(request)
    st = request.app.state.pp
    return {"memory": getattr(c["memory"], "name", "?"), "band": c["band"].name, "messaging": getattr(st.messaging, "mode", "?"),
            "llm_key_present": c["llm"].available, "band_room_configured": bool(getattr(c["band"], "room_id", ""))}
