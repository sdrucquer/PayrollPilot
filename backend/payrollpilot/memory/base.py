"""Memory adapter contract shared by CogneeMemory (real) and InMemoryMemory (dev-only, labeled)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol

DATASET = "pilotco_cases"
MARKER = "PP-RESOLUTION"

_ID_PATTERNS = {
    "resolution_ids": r"\bres_[A-Za-z0-9]+\b",
    "cycle_ids": r"\bcyc_[A-Za-z0-9]+\b",
    "time_entry_ids": r"\bte_[A-Za-z0-9]+\b",
    "job_ids": r"\bjob_[A-Za-z0-9]+\b",
    "cost_ids": r"\bcost_[A-Za-z0-9]+\b",
    "inbound_ids": r"\bmsg_in_[A-Za-z0-9]+\b",
    "worker_ids": r"\bwkr_[A-Za-z0-9]+\b",
}


@dataclass
class MemoryHit:
    text: str
    refs: dict[str, list[str]]
    source: str  # "cognee" | "in_memory_dev"
    score: float | None = None
    raw: Any = field(default=None, repr=False)


class MemoryAdapter(Protocol):
    name: str

    async def write_resolution(self, resolution: dict) -> str: ...

    async def recall(self, query: str, scope: dict) -> list[MemoryHit]: ...


def parse_refs(text: str) -> dict[str, list[str]]:
    """Pull record ids out of memory text. Ids are data; they are re-validated against current records."""
    out: dict[str, list[str]] = {}
    for key, pat in _ID_PATTERNS.items():
        found = list(dict.fromkeys(re.findall(pat, text)))
        if found:
            out[key] = found
    # Off-site parent relation is written as "(off-site child of job_X)".
    m = re.search(r"off-site child of (job_[A-Za-z0-9]+)", text)
    if m:
        out["offsite_parent_job_ids"] = [m.group(1)]
    return out


def memory_text_for_resolution(res: dict) -> str:
    """Scoped, minimal sentence for memory. No names, phone numbers, rates or amounts."""
    facts = res.get("confirmed_facts", {})
    scope = res.get("scope", {})
    parts = [
        f"{MARKER} {res['id']}",
        f"company {scope.get('company_label', 'Pilot Co')}",
        f"cycle {res.get('cycle_id') or scope.get('cycle_id')}",
        f"exception {res.get('exception_id')}",
    ]
    te, job = facts.get("time_entry_id"), facts.get("job_id")
    if te and job:
        fact = f"fact: time entry {te} belongs to job {job}"
        if facts.get("offsite_parent_job_id"):
            fact += f" (off-site child of {facts['offsite_parent_job_id']})"
        if facts.get("site_note"):
            fact += f"; {facts['site_note']}"
        parts.append(fact)
    elif job and facts.get("offsite_parent_job_id"):
        parts.append(f"fact: job {job} is off-site work (off-site child of {facts['offsite_parent_job_id']}); "
                     f"costs on {job} belong to {facts['offsite_parent_job_id']}")
    else:
        parts.append("fact: " + ", ".join(f"{k}={v}" for k, v in sorted(facts.items())))
    inbound = ",".join(res.get("inbound_ids", []))
    parts.append(f"confirmed by {res.get('confirmer_actual', 'owner_test_phone')} reply {inbound} on {str(res.get('created_at', ''))[:10]}")
    ev = ",".join(f"{e.get('system')}:{e.get('record_id')}" for e in res.get("evidence", []))
    parts.append(f"evidence {ev or 'none'}")
    return " | ".join(parts) + "."


class InMemoryMemory:
    """DEV ONLY. Not Cognee. /api/health must report memory=in_memory_dev when this is active."""

    name = "in_memory_dev"

    def __init__(self) -> None:
        self._items: list[str] = []

    async def write_resolution(self, resolution: dict) -> str:
        self._items.append(memory_text_for_resolution(resolution))
        return f"mem_dev_{len(self._items)}"

    async def recall(self, query: str, scope: dict) -> list[MemoryHit]:
        words = {w for w in re.findall(r"[a-z0-9_]+", query.lower()) if len(w) > 3}
        hits = []
        for t in self._items:
            overlap = len(words & set(re.findall(r"[a-z0-9_]+", t.lower())))
            if overlap:
                hits.append(MemoryHit(text=t, refs=parse_refs(t), source=self.name, score=float(overlap)))
        return sorted(hits, key=lambda h: -(h.score or 0))
