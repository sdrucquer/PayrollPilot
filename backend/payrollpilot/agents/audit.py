"""Audit agent: investigation note + respondent proposal only. It cannot create money facts."""
from __future__ import annotations

_DEFAULT_ROLE = {"quote_attribution": "owner", "policy_missing": "owner", "rate_unconfirmed": "owner", "identity": "owner"}


def propose_respondent(exc: dict) -> str:
    return exc.get("intended_respondent_role") or _DEFAULT_ROLE.get(exc.get("category", ""), "ops_lead")


def investigation_note(exc: dict) -> str:
    refs = exc.get("entity_refs") or {}
    parts = [f"{exc['category']}: {exc['title']}"]
    if refs.get("time_entry_ids"):
        parts.append("time entries " + ", ".join(refs["time_entry_ids"]))
    if refs.get("job_ids"):
        parts.append("jobs " + ", ".join(refs["job_ids"]))
    parts.append(f"ask {propose_respondent(exc)}")
    return "; ".join(parts)
