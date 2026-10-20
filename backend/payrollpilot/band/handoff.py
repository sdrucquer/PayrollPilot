"""Case handoffs in the Band room. Pure orchestration over a band adapter; state lives in SQLite (lane A)."""
from __future__ import annotations

import time


def case_card(exc: dict) -> str:
    """Minimized case card: ids, category, title, stage impact. No names, phones or rates."""
    si = exc.get("stage_impact", {})
    prov = exc.get("provenance", "unknown")
    return (
        f"[handoff.requested] audit -> resolution\n"
        f"case {exc['id']} ({prov}) | category {exc.get('category')} | \"{exc.get('title', '')}\"\n"
        f"stage impact: stage1 {si.get('stage1_wages', 'none')}, stage2 {si.get('stage2_costs', 'none')} | "
        f"respondent: {exc.get('intended_respondent_role', 'unknown')} (test mode: owner's allowlisted handle)\n"
        f"@sdrucquer/pp-resolution please take this case."
    )


def _wait_for(band, agent: str, message_id: str, tries: int = 10, delay: float = 1.0) -> dict | None:
    for _ in range(tries):
        for m in band.inbox(agent):
            if m.get("message_id") == message_id:
                return m
        time.sleep(delay)
    return None


def handoff_to_resolution(band, exc: dict, sleep: float = 1.0) -> dict:
    """pp-audit posts the card and a board task; pp-resolution receives, replies (settles), takes the task."""
    card_id = band.post("pp-audit", case_card(exc))
    uid = band.assign("pp-audit", f"{exc['id']} {exc.get('category')}: resolve via owner reply",
                      f"{exc.get('provenance', 'unknown')}; audit -> resolution -> payroll")
    received = _wait_for(band, "pp-resolution", card_id, delay=sleep)
    if received is None:
        return {"accepted": False, "band_message_id": card_id, "task_uid": uid, "reason": "not_delivered"}
    reply_id = band.reply("pp-resolution", card_id,
                          f"[handoff.accepted] resolution owns {exc['id']}. Drafting a question; send waits for owner approval.")
    band.take("pp-resolution", uid)
    band.set_status("pp-resolution", uid, "in_progress")
    return {"accepted": True, "band_message_id": card_id, "reply_message_id": reply_id, "task_uid": uid}


def request_owner_decision(band, batch_id: str, text_hash: str, summary: str) -> str:
    return band.post(
        "pp-resolution",
        f"[decision.requested] @sdrucquer Owner decision: {summary}\n"
        f"Reply 'approve {batch_id}' or 'reject {batch_id}' (text hash {text_hash[:19]}). "
        f"Recorded as an Approval only through the backend approvals route.",
    )


def deliver_to_payroll(band, exc: dict, correction: dict, task_uid: str | None, sleep: float = 1.0) -> dict:
    msg = (f"[correction.applied] resolution -> payroll\ncase {exc['id']} | correction {correction['id']} "
           f"({correction.get('kind')}) applied locally; recompute readiness.\n@sdrucquer/pp-payroll")
    mid = band.post("pp-resolution", msg)
    received = _wait_for(band, "pp-payroll", mid, delay=sleep)
    reply_id = None
    if received is not None:
        reply_id = band.reply("pp-payroll", mid, f"[handoff.accepted] payroll recomputing readiness for {exc['id']}.")
    if task_uid:
        band.set_status("pp-resolution", task_uid, "completed")
    return {"band_message_id": mid, "reply_message_id": reply_id, "received": received is not None}
