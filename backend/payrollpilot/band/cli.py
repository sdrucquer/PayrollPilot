"""Thin wrapper over ~/.local/bin/band. Verified commands (2026-10-20, Band 0.4.16): onboard, chat new,
send --body-file, inbox --json, reply, work assign/take/room-status/board, usage. `band ask` returns null
immediately for generic peers (no HITL post), so owner decisions use a room message + inbox reply instead.

Band carries coordination only. It never grants permission: a decision parsed here is a *request* that the
route must turn into an Approval through the normal approvals path (which re-checks the target version).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

AGENTS = ("pp-audit", "pp-resolution", "pp-payroll")
DEFAULT_BIN = str(Path.home() / ".local/bin/band")
_DECISION_RE = re.compile(r"\b(approve|reject)\s+(msg_batch_[A-Za-z0-9_]+|corr_[A-Za-z0-9_]+)\b", re.I)


class BandError(RuntimeError):
    pass


class BandRequired(RuntimeError):
    """Raised when Band is disabled: the case cannot move (route maps to 503 band_required)."""


def parse_decision(message: dict, target_id: str) -> str | None:
    """Return 'approve'|'reject' only for a human (User) message naming exactly this target. Data, not instructions."""
    if message.get("sender_type") != "User":
        return None
    text = re.sub(r"@\[\[[^\]]+\]\]|@\S+", " ", message.get("content", ""))
    found = {(m.group(1).lower(), m.group(2)) for m in _DECISION_RE.finditer(text)}
    decisions = {d for d, t in found if t == target_id}
    if len(decisions) != 1:  # none, or both approve and reject -> no decision
        return None
    return decisions.pop()


class CliBand:
    name = "band_cli"
    enabled = True

    def __init__(self, room_id: str | None = None, bin_path: str | None = None,
                 runner: Callable[..., Any] = subprocess.run, owner_handle: str | None = None) -> None:
        self.bin = bin_path or os.environ.get("PP_BAND_BIN", DEFAULT_BIN)
        self.room_id = room_id or os.environ.get("PP_BAND_ROOM_ID", "")
        self.owner = owner_handle or os.environ.get("PP_BAND_OWNER_HANDLE", "")
        self._run_proc = runner

    # -- plumbing --
    def _run(self, *args: str, timeout: int = 60) -> str:
        proc = self._run_proc([self.bin, *args], capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            raise BandError(f"band {args[0]} failed: {(proc.stderr or proc.stdout).strip()[:300]}")
        return (proc.stdout or "").strip()

    def _need_room(self) -> str:
        if not self.room_id:
            raise BandError("PP_BAND_ROOM_ID not set")
        return self.room_id

    # -- peers / room --
    def ensure_peers(self, host_pid: int) -> list[str]:
        """Bring the three product peers online bound to a live host process (the backend)."""
        return [self._run("onboard", "--host", "generic", "--name", a, "--session", a,
                          "--host-pid", str(host_pid), "--receiver", "pull", "--json", timeout=120) for a in AGENTS]

    def create_room(self) -> str:
        args = ["chat", "new", "--session", "pp-audit", "--with", "sdrucquer/pp-resolution", "--with", "sdrucquer/pp-payroll"]
        if self.owner:
            args += ["--with", self.owner]
        self.room_id = self._run(*args).splitlines()[-1].strip()
        return self.room_id

    # -- messages --
    def post(self, agent: str, text: str) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(text)
            path = f.name
        try:
            out = self._run("send", self._need_room(), "--body-file", path, "--session", agent)
        finally:
            os.unlink(path)
        return out.split()[-1]  # "sent <message_id>"

    def inbox(self, agent: str) -> list[dict]:
        out = self._run("inbox", "--session", agent, "--room", self._need_room(), "--json")
        return json.loads(out) if out.startswith("[") else []

    def reply(self, agent: str, message_id: str, text: str) -> str:
        return self._run("reply", message_id, text, "--session", agent).split()[-1]

    def ack(self, agent: str, message_id: str) -> None:
        self._run("ack", message_id, "--session", agent)

    # -- shared board --
    def assign(self, agent: str, subject: str, detail: str = "") -> str:
        out = self._run("work", "assign", self._need_room(), subject, "--detail", detail, "--session", agent)
        return out.split()[0]  # "#N subject"

    def take(self, agent: str, uid: str) -> None:
        self._run("work", "take", self._need_room(), uid, "--session", agent)

    def set_status(self, agent: str, uid: str, status: str) -> None:
        self._run("work", "room-status", self._need_room(), uid, status, "--session", agent)

    def board(self) -> str:
        return self._run("work", "board", self._need_room(), "--session", "pp-audit")

    def find_decision(self, agent: str, target_id: str) -> dict | None:
        for m in self.inbox(agent):
            d = parse_decision(m, target_id)
            if d:
                return {"decision": d, "band_message_id": m.get("message_id"), "sender_handle": m.get("sender_handle")}
        return None


class NullBand:
    """Band disabled. Demo requires Band, so every coordination call refuses (route returns 503 band_required)."""

    name = "null_band"
    enabled = False

    def __getattr__(self, item: str):
        def refuse(*_a, **_k):
            raise BandRequired("band_required")
        return refuse


def get_band() -> CliBand | NullBand:
    return CliBand() if os.environ.get("PP_BAND_ENABLED") == "1" else NullBand()
