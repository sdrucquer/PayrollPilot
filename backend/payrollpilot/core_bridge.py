"""Import shim for lane B's pure core. If ``payrollpilot_core`` is not
installed yet, the backend runs with a labeled stub (``/api/health`` shows
``audit: "stub"``) instead of pretending audits ran."""

from __future__ import annotations

from typing import Any, Callable

try:  # pragma: no cover - depends on lane B being installed
    from payrollpilot_core.audit import run_audit as _run_audit  # type: ignore

    AUDIT_MODE = "core"
except Exception:  # ImportError or a partial package
    _run_audit = None
    AUDIT_MODE = "stub"


def run_audit(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    if _run_audit is None:
        return []
    return list(_run_audit(snapshot))


def audit_fn() -> Callable[[dict[str, Any]], list[dict[str, Any]]]:
    return run_audit
