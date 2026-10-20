"""Memory adapters. ``InMemoryMemory`` is dev-only and labeled; ``CogneeMemory``
is implemented by lane C in ``payrollpilot/memory/`` and wired here by env.
Memory is never read for amounts (ARCHITECTURE section 4)."""

from __future__ import annotations

from typing import Any


class InMemoryMemory:
    mode = "inmemory"
    label = "IN-MEMORY memory (dev only, not Cognee)"

    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def remember(self, text: str, scope: dict[str, Any], ref: str) -> str:
        mem_id = f"mem_{len(self.items) + 1:04d}"
        self.items.append({"id": mem_id, "text": text, "scope": scope, "ref": ref})
        return mem_id

    def recall(self, query: str, scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        q = query.lower()
        hits = [m for m in self.items if any(tok in m["text"].lower() for tok in q.split())]
        if scope:
            hits = [m for m in hits if all(m["scope"].get(k) == v for k, v in scope.items() if v is not None)]
        return hits
