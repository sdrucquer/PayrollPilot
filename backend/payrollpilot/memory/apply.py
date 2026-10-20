"""Deterministic rule that lets a recalled resolution change a case's next action.

A recall hit never creates an approval or a money fact. It can only change next_action from
"ask again" to "propose X pending owner approval", and only when every id it cites exists in the
current records and the scope (company + parent job) matches.
"""
from __future__ import annotations

from .base import MARKER, MemoryHit

ASK_AGAIN = "ask ops lead which job"


def apply_recall(case: dict, hits: list[MemoryHit], known: dict[str, set[str]]) -> dict:
    """case: {exception_id, cycle_id, company_label, parent_job_id, next_action}
    known: current record ids, e.g. {"job_ids": {...}, "time_entry_ids": {...}, "resolution_ids": {...}}
    Returns {applied, next_action_before, next_action_after, used_hit, rejected: [{reason, text}]}.
    """
    before = case.get("next_action") or ASK_AGAIN
    rejected: list[dict] = []
    for hit in hits:
        refs = hit.refs
        reason = _reject_reason(hit, case, known)
        if reason:
            rejected.append({"reason": reason, "text": hit.text[:200]})
            continue
        job = _target_job(refs, case)
        return {
            "applied": True,
            "next_action_before": before,
            "next_action_after": f"propose allocation to {job} pending owner approval",
            "proposed": {"job_id": job, "based_on_resolution_ids": refs.get("resolution_ids", [])},
            "used_hit": {"text": hit.text, "refs": refs, "source": hit.source},
            "rejected": rejected,
            "approval_created": False,
        }
    return {
        "applied": False,
        "next_action_before": before,
        "next_action_after": before,
        "state": "insufficient_evidence",
        "used_hit": None,
        "rejected": rejected,
        "approval_created": False,
    }


def _target_job(refs: dict, case: dict) -> str | None:
    child = case.get("offsite_child_job_id")
    if child:  # a cost on an off-site child job is allocated to its confirmed parent
        parents = refs.get("offsite_parent_job_ids", [])
        return parents[0] if parents and child in refs.get("job_ids", []) else None
    parent = case.get("parent_job_id")
    for j in refs.get("job_ids", []):
        if j != parent:
            return j
    return None


def _reject_reason(hit: MemoryHit, case: dict, known: dict[str, set[str]]) -> str | None:
    if MARKER not in hit.text:
        return "not_a_resolution_memory"
    refs = hit.refs
    if not refs.get("resolution_ids"):
        return "no_resolution_id"
    if case.get("company_label") and f"company {case['company_label']}" not in hit.text:
        return "company_scope_mismatch"
    for key in ("resolution_ids", "job_ids", "time_entry_ids"):
        unknown = [i for i in refs.get(key, []) if i not in known.get(key, set())]
        if unknown:
            return f"unknown_{key}:{','.join(unknown)}"
    parent = case.get("parent_job_id")
    if parent and parent not in refs.get("offsite_parent_job_ids", []):
        return "parent_job_mismatch"
    if not _target_job(refs, case):
        return "no_target_job"
    return None
