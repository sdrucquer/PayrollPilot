"""Approval creation (owner action). An approval binds to the exact current
version of its target; creating one for a stale version is refused. A newer
approval for the same target invalidates older active ones."""

from __future__ import annotations

from typing import Any

from . import kinds
from .db import Database, now_iso
from .events import emit, new_id
from .permissions import PermissionDenied, assert_not_gated, batch_version, correction_version

# Approval kinds whose effect has no executor in this pilot.
_GATED_KIND_ACTION = {"source_write": "source_write", "payroll_draft": "payroll_draft"}


class ApprovalError(Exception):
    def __init__(self, status: int, code: str, detail: str, extra: dict[str, Any] | None = None) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail
        self.extra = extra or {}


def source_versions_for_correction(db: Database, correction: dict[str, Any]) -> dict[str, str]:
    """version_hash of every time entry the correction touches, from the
    current snapshot of its cycle. Missing hashes stay out (no invention)."""
    cycle_id = correction.get("cycle_id")
    if not cycle_id:
        return {}
    snap = db.get_record(kinds.SNAPSHOT, cycle_id)
    if not snap:
        return {}
    entries = {te["id"]: te for te in snap["data"].get("time_entries") or []}
    ids = set()
    for side in (correction.get("before") or {}, correction.get("after") or {}):
        if side.get("time_entry_id"):
            ids.add(side["time_entry_id"])
    return {i: entries[i]["version_hash"] for i in sorted(ids) if i in entries and entries[i].get("version_hash")}


def current_target_version(db: Database, kind: str, target_id: str) -> str:
    if kind == "message_send":
        batch = db.get_record(kinds.MESSAGE_BATCH, target_id)
        if batch is None:
            raise ApprovalError(404, "target_not_found", f"message batch {target_id} not found")
        if batch.get("declined_at"):
            raise ApprovalError(409, "batch_declined", "owner declined this message")
        return batch_version(batch)
    if kind == "local_correction":
        corr = db.get_record(kinds.CORRECTION, target_id)
        if corr is None:
            raise ApprovalError(404, "target_not_found", f"correction {target_id} not found")
        return correction_version(corr, source_versions_for_correction(db, corr))
    if kind == "estimate":
        raise ApprovalError(501, "not_implemented", "estimate approvals have no target store yet")
    raise ApprovalError(400, "bad_kind", f"unknown approval kind {kind!r}")


def create_approval(db: Database, *, kind: str, target_id: str, target_version: str, scope_text: str) -> dict[str, Any]:
    if kind in _GATED_KIND_ACTION:
        assert_not_gated(_GATED_KIND_ACTION[kind])  # raises NotImplementedError("gated: P1 ...")
    if not scope_text.strip():
        raise ApprovalError(422, "scope_text_required", "scope_text must state exactly what is approved")
    current = current_target_version(db, kind, target_id)
    if target_version != current:
        raise ApprovalError(409, "stale_version", "target changed; review the current version and approve again",
                            {"current_version": current})

    target_kind = kinds.MESSAGE_BATCH if kind == "message_send" else kinds.CORRECTION
    target = db.get_record(target_kind, target_id) or {}
    cycle_id = target.get("cycle_id")

    for old in db.approvals_for_target(target_id, state="active"):
        old = dict(old, state="invalidated", invalidated_reason=f"superseded by a newer approval for {target_version}")
        db.put_approval(old)
        emit(db, type="approval.invalidated", actor="system", cycle_id=cycle_id,
             summary=f"Approval {old['id']} superseded", refs={"approval_id": old["id"], "target_id": target_id})

    approval = {
        "id": new_id("appr"),
        "kind": kind,
        "target_id": target_id,
        "target_version": target_version,
        "approver": "owner",
        "approved_at": now_iso(),
        "scope_text": scope_text,
        "state": "active",
        "invalidated_reason": None,
    }
    db.put_approval(approval)

    # Reflect the approval on the target as a new record version (append-only).
    if target:
        updated = {k: v for k, v in target.items() if k != "_version"}
        updated["approval_id"] = approval["id"]
        if kind == "message_send" and updated.get("state") == "draft":
            updated["state"] = "approved"
        if kind == "local_correction" and updated.get("state") == "proposed":
            updated["state"] = "approved"
        db.put_record(target_kind, updated)

    emit(db, type="approval.granted", actor="owner", cycle_id=cycle_id,
         summary=f"Owner approved {kind} {target_id}",
         refs={"approval_id": approval["id"], "kind": kind, "target_id": target_id, "target_version": target_version})
    return approval


def invalidate_for_target(db: Database, target_id: str, reason: str, cycle_id: str | None = None) -> list[str]:
    """Called when a target or its source records change (T16)."""
    ids = []
    for appr in db.approvals_for_target(target_id, state="active"):
        db.put_approval(dict(appr, state="invalidated", invalidated_reason=reason))
        emit(db, type="approval.invalidated", actor="system", cycle_id=cycle_id,
             summary=f"Approval {appr['id']} invalidated: {reason}", refs={"approval_id": appr["id"], "target_id": target_id})
        ids.append(appr["id"])
    return ids


def require_active_approval(db: Database, approval_id: str | None) -> dict[str, Any]:
    if not approval_id:
        raise PermissionDenied("approval.missing", "no approval attached")
    appr = db.get_approval(approval_id)
    if appr is None:
        raise PermissionDenied("approval.missing", f"approval {approval_id} not found")
    return appr
