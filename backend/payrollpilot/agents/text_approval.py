"""Version-bound owner confirmations over the authenticated, allowlisted bridge.

These are approval requests, not agent permissions. Every approval is created by
approvals.create_approval; sends/applications still use the existing permission gates.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
from typing import Any
import re
import secrets

from .. import approvals, kinds
from ..db import now_iso
from ..events import emit, new_id
from ..permissions import batch_version, check_recipient, text_hash
from ..settings import mask_handle
from .guard import unauthorized_instruction
from .resolution import _demo_job_reference

REQUEST_KIND = "text_approval_request"
COMMAND = re.compile(r"\s*(APPROVE|REJECT)\s+([A-F0-9]{8})\s*", re.I)


class TextApprovalError(Exception):
    def __init__(self, status: int, code: str, detail: str) -> None:
        self.status, self.code, self.detail = status, code, detail
        super().__init__(detail)


def _update(db: Any, kind: str, record: dict, **changes: Any) -> dict:
    return db.put_record(kind, {**{k: v for k, v in record.items() if k != "_version"}, **changes})


def _target(st: Any, kind: str, target_id: str) -> tuple[dict, str]:
    if kind not in {"message_send", "local_correction"}:
        raise TextApprovalError(422, "unsupported_kind", "Only message sends and local corrections support phone approval")
    rec = st.db.get_record(kinds.MESSAGE_BATCH if kind == "message_send" else kinds.CORRECTION, target_id)
    if not rec:
        raise TextApprovalError(404, "target_not_found", "Proposal not found")
    required = "draft" if kind == "message_send" else "proposed"
    send_state = st.db.send_state(target_id) if kind == "message_send" else None
    if (rec.get("state") != required or rec.get("declined_at") or rec.get("text_approval_request_id")
            or (send_state and send_state["state"] in {"sending", "sent"})):
        raise TextApprovalError(409, "target_not_pending", "Proposal is no longer awaiting approval")
    if kind == "message_send":
        check_recipient(rec.get("actual_recipient"), st.settings.allowlist)
    return rec, approvals.current_target_version(st.db, kind, target_id)


def _money(cents: int | None) -> str:
    return "unknown" if cents is None else f"${Decimal(cents) / Decimal(100):,.2f}"


def _summary(kind: str, target: dict) -> str:
    if kind == "message_send":
        return "Approve sending this exact message to your allowlisted test phone:\n" + target["text"]
    # Show stored facts/impact; never infer unknown money or a new allocation.
    def facts(values: dict | None) -> str:
        return "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in (values or {}).items()) or "not specified"
    impact = target.get("calculation_impact") or {}
    jobs = impact.get("job_costing_delta") or []
    costs = "; ".join(f"{j['job_id']}: {_money(j.get('labor_delta_cents', j.get('cost_delta_cents')))}" for j in jobs) or "not specified"
    return (f"Approve local correction {target['id']}:\nBefore: {facts(target.get('before'))}"
            f"\nAfter: {facts(target.get('after'))}\nEmployee wages change: {_money(impact.get('stage1_wages_delta_cents'))}"
            f"\nJob cost changes: {costs}\nThis changes PayrollPilot only; source systems stay read-only.")


def _exceptions(st: Any, target: dict) -> list[str]:
    ids = list(target.get("exception_ids") or [])
    resolution = st.db.get_record(kinds.RESOLUTION, target.get("resolution_id")) if target.get("resolution_id") else None
    if resolution:
        ids.append(resolution["exception_id"])
    if not ids:
        entry = (target.get("after") or {}).get("time_entry_id")
        if entry:
            ids.extend(e["id"] for e in st.db.list_records(kinds.EXCEPTION, cycle_id=target.get("cycle_id"))
                       if entry in (e.get("entity_refs") or {}).get("time_entry_ids", []))
    return list(dict.fromkeys(ids))


def _batch(st: Any, req: dict, *, followup: bool = False) -> dict:
    text = ("Please confirm the specific proposal; your previous reply did not approve anything.\n" if followup else "PayrollPilot owner approval request:\n")
    text += req["summary"] + "\n"
    excs = [st.db.get_record(kinds.EXCEPTION, i) for i in req["exception_ids"]]
    text += "\n".join(_demo_job_reference([e for e in excs if e]))
    expiry = datetime.fromisoformat(req["expires_at"]).astimezone(ZoneInfo("America/Los_Angeles")).strftime("%I:%M %p").lstrip("0")
    text += (f"\nReply APPROVE {req['code']} to approve only this exact proposal, or REJECT {req['code']}. "
             f"This code expires at {expiry} Pacific. A plain yes does not approve. "
             "Sending or applying the approved proposal is a separate step in the app.")
    batch = {"id": new_id("msg_batch"), "cycle_id": req["cycle_id"], "exception_ids": req["exception_ids"],
             "intended_respondent_role": "owner", "intended_respondent_label": "Owner", "actual_recipient": st.settings.test_recipient,
             "channel": "imessage", "text": text, "text_hash": text_hash(text), "approval_id": None, "state": "draft",
             "provider_message_id": None, "sent_at": None, "provider_status": None, "provenance": "synthetic" if st.messaging.mode == "fake" else "real",
             "wording": "template", "parent_batch_id": req.get("review_batch_id"), "created_at": now_iso(), "text_approval_request_id": req["id"]}
    st.db.put_record(kinds.MESSAGE_BATCH, batch)
    emit(st.db, type="message.drafted", actor="resolution", cycle_id=req["cycle_id"],
         summary="Drafted owner phone confirmation; normal send approval is still required",
         refs={"batch_id": batch["id"], "text_approval_request_id": req["id"], "target_id": req["target_id"], "followup": followup})
    return batch


def draft_request(st: Any, kind: str, target_id: str) -> dict:
    check_recipient(st.settings.test_recipient, st.settings.allowlist)
    target, version = _target(st, kind, target_id)
    code = secrets.token_hex(4).upper()
    while st.db.get_record(REQUEST_KIND, "tap_" + code):
        code = secrets.token_hex(4).upper()
    req = {"id": "tap_" + code, "code": code, "kind": kind, "target_id": target_id, "target_version": version,
           "cycle_id": target["cycle_id"], "exception_ids": _exceptions(st, target), "summary": _summary(kind, target),
           "state": "pending", "created_at": now_iso(), "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()}
    batch = _batch(st, req)
    req.update(review_batch_id=batch["id"], review_text_hash=batch_version(batch))
    st.db.put_record(REQUEST_KIND, req)
    return batch


def command_request(db: Any, text: str) -> dict | None:
    match = COMMAND.fullmatch(text)
    return db.get_record(REQUEST_KIND, "tap_" + match[2].upper()) if match else None


def handle_reply(st: Any, inbound: dict, batch: dict | None) -> dict | None:
    """Return None for ordinary factual replies; an approval-like reply never reaches an LLM."""
    raw = inbound["raw_text"]
    req = command_request(st.db, raw)
    req = req or (st.db.get_record(REQUEST_KIND, batch.get("text_approval_request_id")) if batch and batch.get("text_approval_request_id") else None)
    if not req:
        if re.match(r"\s*(approve|reject)\b", raw, re.I):
            raise TextApprovalError(409, "approval_request_unknown", "Reply to a sent approval request using its exact confirmation code")
        return None
    if (inbound.get("respondent_actual") != "owner_test_phone"
            or inbound.get("sender") != mask_handle(st.settings.test_recipient)
            or inbound.get("provenance") != "test_reply"):
        raise TextApprovalError(403, "owner_identity_required", "Phone approval requires the authenticated allowlisted owner bridge")
    check_recipient(st.settings.test_recipient, st.settings.allowlist)
    if req["state"] != "pending":
        raise TextApprovalError(409, "approval_request_consumed", "This request has already been decided")
    if datetime.now(timezone.utc) >= datetime.fromisoformat(req["expires_at"]):
        raise TextApprovalError(409, "approval_request_expired", "Review a fresh approval request")
    review = st.db.get_record(kinds.MESSAGE_BATCH, req["review_batch_id"])
    sent = st.db.send_state(req["review_batch_id"])
    if not review or review.get("state") != "sent" or not sent or sent["state"] != "sent":
        raise TextApprovalError(409, "approval_request_not_sent", "The owner must receive the reviewed proposal first")
    if batch_version(review) != req["review_text_hash"]:
        raise TextApprovalError(409, "approval_request_changed", "The request text changed; review a fresh request")
    _, current = _target(st, req["kind"], req["target_id"])
    if current != req["target_version"]:
        raise TextApprovalError(409, "stale_version", "The proposal or its source changed; review a fresh request")
    blocked = unauthorized_instruction(raw)
    if blocked:
        emit(st.db, type="blocked.unauthorized_instruction", actor="resolution", cycle_id=req["cycle_id"],
             summary="Phone approval reply contained an unauthorized instruction; nothing approved", refs={"inbound_id": inbound["id"], "codes": blocked})
        return {"approval": None, "blocked": blocked, "exception_updates": []}
    match = COMMAND.fullmatch(raw)
    if not match or match[2].upper() != req["code"]:
        prior = st.db.get_record(kinds.MESSAGE_BATCH, req.get("followup_batch_id")) if req.get("followup_batch_id") else None
        followup = prior or _batch(st, req, followup=True)
        if not prior:
            _update(st.db, REQUEST_KIND, req, followup_batch_id=followup["id"])
        emit(st.db, type="clarification.needed", actor="resolution", cycle_id=req["cycle_id"],
             summary="Phone approval was vague or did not match; drafted explicit confirmation without approving",
             refs={"inbound_id": inbound["id"], "batch_id": followup["id"], "target_id": req["target_id"]})
        return {"approval": None, "needs_confirmation": True, "followup_batch_id": followup["id"], "exception_updates": []}
    if match[1].upper() == "REJECT":
        _update(st.db, REQUEST_KIND, req, state="rejected", inbound_id=inbound["id"])
        return {"approval": None, "decision": "reject", "exception_updates": []}
    approval = approvals.create_approval(st.db, kind=req["kind"], target_id=req["target_id"], target_version=req["target_version"],
                                         scope_text=f"Owner approved the exact version reviewed in phone request {req['id']} via inbound {inbound['id']}; approve only, no send/apply")
    _update(st.db, REQUEST_KIND, req, state="approved", approval_id=approval["id"], inbound_id=inbound["id"])
    return {"approval": approval, "decision": "approve", "exception_updates": [], "applied": False, "sent": False}
