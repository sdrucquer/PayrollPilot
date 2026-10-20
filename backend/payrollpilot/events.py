"""Append-only event log (CONTRACTS section 4)."""

from __future__ import annotations

import uuid
from typing import Any

from .db import Database, now_iso

EVENT_TYPES = frozenset(
    {
        "cycle.created", "snapshot.captured", "audit.completed", "exception.detected", "exception.state_changed",
        "handoff.requested", "handoff.accepted", "message.drafted", "approval.granted", "approval.invalidated",
        "message.sent", "message.delivery_status", "message.received", "reply.parsed", "clarification.needed",
        "resolution.recorded", "memory.written", "memory.recalled", "memory.applied", "correction.proposed",
        "correction.applied", "recalc.completed", "readiness.changed", "workbook.generated", "workbook.verified",
        "blocked.unauthorized_instruction", "budget.exhausted", "run.stopped",
    }
)

ACTORS = frozenset({"audit", "resolution", "payroll", "owner", "system", "bridge"})


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def emit(
    db: Database,
    *,
    type: str,
    actor: str,
    summary: str,
    cycle_id: str | None = None,
    refs: dict[str, Any] | None = None,
    usage: dict[str, Any] | None = None,
    duration_ms: int | None = None,
) -> dict[str, Any]:
    if type not in EVENT_TYPES:
        raise ValueError(f"unknown event type: {type}")
    if actor not in ACTORS:
        raise ValueError(f"unknown actor: {actor}")
    event = {
        "id": new_id("evt"),
        "at": now_iso(),
        "cycle_id": cycle_id,
        "actor": actor,
        "type": type,
        "summary": summary,
        "refs": refs or {},
        "usage": usage,
        "duration_ms": duration_ms,
    }
    return db.append_event(event)
