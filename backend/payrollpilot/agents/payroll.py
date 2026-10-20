"""Payroll Preparation agent: before acting on a related item it recalls memory; a validated hit can change
next_action (memory.applied). It never creates approvals; owner decisions go through the approvals route."""
from __future__ import annotations

from ..memory.apply import apply_recall


async def next_action_with_memory(memory, case: dict, known: dict[str, set[str]]) -> dict:
    hits = await memory.recall(case["query"], {"company_label": case.get("company_label")}) if memory else []
    out = apply_recall(case, hits, known)
    out["hit_count"] = len(hits)
    out["memory_adapter"] = getattr(memory, "name", "disabled")
    return out
