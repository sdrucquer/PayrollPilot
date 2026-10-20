"""Import shim for lane B's pure core. Missing pieces run as labeled stubs
(``/api/health`` shows which) instead of pretending work happened.

Expected signatures (docs/plans/B-audit-payroll.md):
  audit.run_audit(snapshot) -> list[Exception dict]
  corrections.propose_correction(kind, before, after, snapshot) -> LocalCorrection dict
  readiness.cycle_readiness(snapshot, exceptions, policies=None) -> {stage1, workers, items, items_by_id, stage2_summary}
  packet.build_packet(cycle, workers, entries, items, exceptions, corrections) -> dict
  workbook.build_workbook(packet, path) -> WorkbookArtifact dict
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Optional


def _load(module: str, name: str) -> Optional[Callable[..., Any]]:
    try:
        mod = importlib.import_module(f"payrollpilot_core.{module}")
    except Exception:
        return None
    fn = getattr(mod, name, None)
    return fn if callable(fn) else None


_run_audit = _load("audit", "run_audit")
AUDIT_MODE = "core" if _run_audit else "stub"

propose_correction = _load("corrections", "propose_correction")
cycle_readiness = _load("readiness", "cycle_readiness")
build_packet = _load("packet", "build_packet")
build_workbook = _load("workbook", "build_workbook")


def run_audit(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    if _run_audit is None:
        return []
    return list(_run_audit(snapshot))


def modes() -> dict[str, str]:
    return {
        "audit": AUDIT_MODE,
        "corrections": "core" if propose_correction else "missing",
        "readiness": "core" if cycle_readiness else "missing",
        "packet": "core" if build_packet else "missing",
        "workbook": "core" if build_workbook else "missing",
    }
