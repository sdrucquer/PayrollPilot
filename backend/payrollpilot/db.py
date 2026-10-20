"""SQLite persistence (ARCHITECTURE section 4).

Tables:
  records(kind, id, version, json, created_at)   append new versions; latest = max(version)
  events(id, at, cycle_id, actor, type, json)      append-only
  approvals(id, kind, target_id, target_version, state, json, created_at)
  inbound_dedupe(provider_message_id UNIQUE, inbound_id, received_at)
  send_log(batch_id UNIQUE, provider_message_id, state, sent_at)

Everything is stored as JSON text. Money stays integer cents inside the JSON;
this layer never does arithmetic. Restart-safe by construction: the file is the
state (T18, FR-25).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
  kind TEXT NOT NULL,
  id TEXT NOT NULL,
  version INTEGER NOT NULL,
  json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (kind, id, version)
);
CREATE INDEX IF NOT EXISTS records_kind_idx ON records(kind);
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  at TEXT NOT NULL,
  cycle_id TEXT,
  actor TEXT NOT NULL,
  type TEXT NOT NULL,
  json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_cycle_idx ON events(cycle_id, at);
CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  target_id TEXT NOT NULL,
  target_version TEXT NOT NULL,
  state TEXT NOT NULL,
  json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS approvals_target_idx ON approvals(target_id, state);
CREATE TABLE IF NOT EXISTS inbound_dedupe (
  provider_message_id TEXT PRIMARY KEY,
  inbound_id TEXT NOT NULL,
  received_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS send_log (
  batch_id TEXT PRIMARY KEY,
  provider_message_id TEXT,
  state TEXT NOT NULL,
  sent_at TEXT
);
CREATE TABLE IF NOT EXISTS flags (
  name TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    """Local timestamp with offset, seconds precision (CONTRACTS section 0)."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Database:
    """Thin synchronous wrapper around one SQLite file. Safe for FastAPI's
    threadpool because every call takes a lock; the workload is tiny."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL") if str(self.path) != ":memory:" else None
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._lock = threading.RLock()
        with self._lock:
            self._conn.executescript(SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ---- records -----------------------------------------------------------
    def put_record(self, kind: str, record: dict[str, Any]) -> dict[str, Any]:
        """Append a new version of ``record`` (must carry ``id``). Returns the
        stored dict with ``_version`` set. Records are never updated in place."""
        rid = record["id"]
        with self._lock:
            row = self._conn.execute(
                "SELECT COALESCE(MAX(version), 0) FROM records WHERE kind=? AND id=?", (kind, rid)
            ).fetchone()
            version = int(row[0]) + 1
            stored = dict(record)
            stored["_version"] = version
            self._conn.execute(
                "INSERT INTO records(kind, id, version, json, created_at) VALUES (?,?,?,?,?)",
                (kind, rid, version, dumps(stored), now_iso()),
            )
        return stored

    def put_records(self, kind: str, records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.put_record(kind, r) for r in records]

    def get_record(self, kind: str, rid: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT json FROM records WHERE kind=? AND id=? ORDER BY version DESC LIMIT 1",
                (kind, rid),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def record_versions(self, kind: str, rid: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT json FROM records WHERE kind=? AND id=? ORDER BY version ASC", (kind, rid)
            ).fetchall()
        return [json.loads(r[0]) for r in rows]

    def list_records(self, kind: str, **filters: Any) -> list[dict[str, Any]]:
        """Latest version of every record of ``kind``; optional equality filters
        on top-level JSON keys (``None`` filter values are ignored)."""
        with self._lock:
            rows = self._conn.execute(
                """SELECT r.json FROM records r
                   JOIN (SELECT kind, id, MAX(version) AS v FROM records WHERE kind=? GROUP BY kind, id) m
                     ON r.kind=m.kind AND r.id=m.id AND r.version=m.v
                   ORDER BY r.id""",
                (kind,),
            ).fetchall()
        out = [json.loads(r[0]) for r in rows]
        for key, value in filters.items():
            if value is None:
                continue
            out = [o for o in out if o.get(key) == value]
        return out

    def count_records(self, kind: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(DISTINCT id) FROM records WHERE kind=?", (kind,)
            ).fetchone()
        return int(row[0])

    # ---- events --------------------------------------------------------------
    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._conn.execute(
                "INSERT INTO events(id, at, cycle_id, actor, type, json) VALUES (?,?,?,?,?,?)",
                (event["id"], event["at"], event.get("cycle_id"), event["actor"], event["type"], dumps(event)),
            )
        return event

    def list_events(self, cycle_id: str | None = None, since: str | None = None, limit: int = 1000) -> list[dict[str, Any]]:
        sql = "SELECT json FROM events WHERE 1=1"
        params: list[Any] = []
        if cycle_id:
            sql += " AND cycle_id=?"
            params.append(cycle_id)
        if since:
            sql += " AND at>?"
            params.append(since)
        sql += " ORDER BY at ASC, rowid ASC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [json.loads(r[0]) for r in rows]

    # ---- approvals -----------------------------------------------------------
    def put_approval(self, approval: dict[str, Any]) -> dict[str, Any]:
        """Insert or replace an approval row by id. Approvals move
        active -> invalidated only; callers write a new dict, never mutate."""
        with self._lock:
            self._conn.execute(
                """INSERT INTO approvals(id, kind, target_id, target_version, state, json, created_at)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET state=excluded.state, json=excluded.json""",
                (
                    approval["id"], approval["kind"], approval["target_id"], approval["target_version"],
                    approval["state"], dumps(approval), approval.get("approved_at") or now_iso(),
                ),
            )
        return approval

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT json FROM approvals WHERE id=?", (approval_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def approvals_for_target(self, target_id: str, state: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT json FROM approvals WHERE target_id=?"
        params: list[Any] = [target_id]
        if state:
            sql += " AND state=?"
            params.append(state)
        sql += " ORDER BY created_at ASC"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [json.loads(r[0]) for r in rows]

    def list_approvals(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT json FROM approvals ORDER BY created_at ASC").fetchall()
        return [json.loads(r[0]) for r in rows]

    # ---- dedupe + send log -----------------------------------------------------
    def claim_inbound(self, provider_message_id: str, inbound_id: str) -> bool:
        """Return True if this provider message is new (claimed now); False if seen."""
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO inbound_dedupe(provider_message_id, inbound_id, received_at) VALUES (?,?,?)",
                    (provider_message_id, inbound_id, now_iso()),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def claim_send(self, batch_id: str) -> bool:
        """Return True if the batch has never been sent/claimed; marks it 'sending'."""
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO send_log(batch_id, provider_message_id, state, sent_at) VALUES (?,?,?,?)",
                    (batch_id, None, "sending", None),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def record_send_result(self, batch_id: str, provider_message_id: str | None, state: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE send_log SET provider_message_id=?, state=?, sent_at=? WHERE batch_id=?",
                (provider_message_id, state, now_iso(), batch_id),
            )

    def send_state(self, batch_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT batch_id, provider_message_id, state, sent_at FROM send_log WHERE batch_id=?", (batch_id,)
            ).fetchone()
        if not row:
            return None
        return {"batch_id": row[0], "provider_message_id": row[1], "state": row[2], "sent_at": row[3]}

    # ---- flags (run stop etc.) ------------------------------------------------------
    def set_flag(self, name: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO flags(name, value, updated_at) VALUES (?,?,?) ON CONFLICT(name) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (name, value, now_iso()),
            )

    def get_flag(self, name: str) -> str | None:
        with self._lock:
            row = self._conn.execute("SELECT value FROM flags WHERE name=?", (name,)).fetchone()
        return row[0] if row else None
