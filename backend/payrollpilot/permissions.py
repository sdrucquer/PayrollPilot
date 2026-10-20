"""Code-enforced permissions (shared context section 6, CONTRACTS section 2).

Routes call these. Agents cannot. A Band message, a memory, a web page, or an
inbound text can never grant permission: nothing here reads prompt text.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

GATED_ACTIONS = frozenset({"source_write", "payroll_submit", "payroll_draft", "gusto_draft", "money_transfer"})


class PermissionDenied(Exception):
    """Raised when an effect is not authorized. Routes map this to HTTP 403."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def content_hash(obj: Any) -> str:
    """Stable ``sha256:<hex>`` over canonical JSON. Used for ``target_version``."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_recipient(handle: str, allowlist: Iterable[str]) -> str:
    """Only ``PP_TEST_RECIPIENT`` may receive a message. Returns the handle."""
    allowed = {h.strip() for h in allowlist if h and h.strip()}
    if not allowed:
        raise PermissionDenied("recipient.allowlist_empty", "PP_TEST_RECIPIENT is not configured; no recipient is allowed")
    if not handle or handle.strip() not in allowed:
        raise PermissionDenied("recipient.not_allowlisted", "recipient is not the allowlisted test recipient")
    return handle.strip()


def _check_approval(approval: dict[str, Any] | None, *, kind: str, target_id: str, current_version: str) -> None:
    if approval is None:
        raise PermissionDenied("approval.missing", f"no approval for {target_id}")
    if approval.get("kind") != kind:
        raise PermissionDenied("approval.kind_mismatch", f"approval kind {approval.get('kind')!r} is not {kind!r}")
    if approval.get("target_id") != target_id:
        raise PermissionDenied("approval.target_mismatch", "approval is for a different target")
    if approval.get("state") != "active":
        raise PermissionDenied("approval.not_active", f"approval state is {approval.get('state')!r}")
    if approval.get("target_version") != current_version:
        raise PermissionDenied("approval.version_mismatch", "content changed since approval; re-approval required")


def batch_version(batch: dict[str, Any]) -> str:
    """CONTRACTS: a message approval's ``target_version`` is the batch
    ``text_hash`` = sha256 of the exact text, recomputed here from the text so
    an edited text cannot reuse an old hash. The recipient is bound separately:
    ``check_send`` re-checks it against the allowlist (a single handle)."""
    return text_hash(batch.get("text") or "")


def check_send(batch: dict[str, Any], approval: dict[str, Any] | None, allowlist: Iterable[str]) -> None:
    """Allowlist + approval kind/version/state. Raises PermissionDenied."""
    check_recipient(batch.get("actual_recipient") or "", allowlist)
    if batch.get("channel") not in {"imessage", None}:
        raise PermissionDenied("channel.unsupported", f"channel {batch.get('channel')!r} is not supported")
    _check_approval(approval, kind="message_send", target_id=batch["id"], current_version=batch_version(batch))


def correction_version(correction: dict[str, Any], source_versions: dict[str, str] | None = None) -> str:
    """A correction approval binds to its exact before/after AND to the version
    hashes of the source records it touches, so a source change invalidates it."""
    return content_hash(
        {
            "resolution_id": correction.get("resolution_id"),
            "kind": correction.get("kind"),
            "before": correction.get("before"),
            "after": correction.get("after"),
            "source_versions": source_versions or {},
        }
    )


def check_apply(correction: dict[str, Any], approval: dict[str, Any] | None, source_versions: dict[str, str] | None = None) -> None:
    if correction.get("state") not in {"proposed", "approved"}:
        raise PermissionDenied("correction.not_applicable", f"correction state is {correction.get('state')!r}")
    _check_approval(
        approval,
        kind="local_correction",
        target_id=correction["id"],
        current_version=correction_version(correction, source_versions),
    )


def assert_not_gated(action: str) -> None:
    """Source writes and payroll submission have no executor in this pilot."""
    if action in GATED_ACTIONS:
        raise NotImplementedError(f"gated: P1 ({action} has no executor in this pilot)")
