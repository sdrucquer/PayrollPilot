"""Deterministic coordinator: owns exception state transitions (CONTRACTS section 2).

LLM agents may only *request* a transition; this module decides. Lane C
extends this module (handoff, reply handling) without changing the table.
"""

from __future__ import annotations

from typing import Any

from .db import Database, now_iso
from .events import emit

# detected -> investigating -> awaiting_reply -> answer_received -> needs_approval | needs_source_verification -> resolved
# any -> conflicting | insufficient_evidence | escalated ; resolved -> detected (reopen)
_FORWARD: dict[str, set[str]] = {
    "detected": {"investigating"},
    "investigating": {"awaiting_reply"},
    "awaiting_reply": {"answer_received"},
    "answer_received": {"needs_approval", "needs_source_verification"},
    "needs_approval": {"resolved"},
    "needs_source_verification": {"resolved"},
    "resolved": {"detected"},
    "conflicting": set(),
    "insufficient_evidence": set(),
    "escalated": set(),
}
_ANY_TO = {"conflicting", "insufficient_evidence", "escalated"}
STATES = frozenset(_FORWARD)


class TransitionRejected(Exception):
    def __init__(self, current: str, requested: str) -> None:
        super().__init__(f"transition {current} -> {requested} is not allowed")
        self.current = current
        self.requested = requested


def allowed_transitions(current: str) -> set[str]:
    if current not in _FORWARD:
        raise ValueError(f"unknown state {current!r}")
    return set(_FORWARD[current]) | (_ANY_TO - {current})


def can_transition(current: str, requested: str) -> bool:
    return requested in allowed_transitions(current)


def transition_exception(
    db: Database, exception_id: str, requested: str, *, actor: str, reason: str, next_action: str | None = None
) -> dict[str, Any]:
    exc = db.get_record("exception", exception_id)
    if exc is None:
        raise KeyError(exception_id)
    current = exc["state"]
    if not can_transition(current, requested):
        raise TransitionRejected(current, requested)
    updated = {k: v for k, v in exc.items() if k != "_version"}
    updated["state"] = requested
    updated["updated_at"] = now_iso()
    if next_action is not None:
        updated["next_action"] = next_action
    stored = db.put_record("exception", updated)
    emit(
        db, type="exception.state_changed", actor=actor, cycle_id=exc.get("cycle_id"),
        summary=f"{exception_id}: {current} -> {requested} ({reason})",
        refs={"exception_id": exception_id, "from": current, "to": requested},
    )
    return stored


def is_stopped(db: Database) -> bool:
    return db.get_flag("run_stopped") == "1"
