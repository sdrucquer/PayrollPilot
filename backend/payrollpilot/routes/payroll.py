"""A-04: corrections, readiness, packet, workbook. Thin; core-dependent parts
return 501 {"reason": "core not merged"} until lane B's functions exist."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .. import core_bridge, corrections, cycles, kinds
from ..contracts import CorrectionRequest
from ..coordinator import is_stopped
from ..db import now_iso
from ..events import emit, new_id
from ..settings import load_private_policies

router = APIRouter()


def _501(what: str) -> JSONResponse:
    return JSONResponse(status_code=501, content={"error": "core_not_merged", "reason": "core not merged", "needs": what})


@router.post("/api/corrections")
def propose(body: CorrectionRequest, request: Request):
    db = request.app.state.pp.db
    if is_stopped(db):
        return JSONResponse(status_code=409, content={"error": "run_stopped"})
    extra = body.model_extra or {}
    try:
        return corrections.propose(db, resolution_id=body.resolution_id, kind=body.kind, after=body.after, cycle_id=extra.get("cycle_id"))
    except corrections.CorrectionError as e:
        return JSONResponse(status_code=e.status, content={"error": e.code, "detail": e.detail, "reason": e.detail})


@router.post("/api/corrections/{correction_id}/apply")
def apply(correction_id: str, request: Request):
    db = request.app.state.pp.db
    if is_stopped(db):
        return JSONResponse(status_code=409, content={"error": "run_stopped"})
    try:
        return corrections.apply(db, correction_id, load_private_policies(request.app.state.pp.settings))
    except corrections.CorrectionError as e:
        return JSONResponse(status_code=e.status, content={"error": e.code, "detail": e.detail})


@router.get("/api/corrections/{correction_id}")
def get_correction(correction_id: str, request: Request):
    rec = request.app.state.pp.db.get_record(kinds.CORRECTION, correction_id)
    if rec is None:
        raise HTTPException(404, f"correction {correction_id} not found")
    return corrections.with_target_version(request.app.state.pp.db, rec)


@router.get("/api/cycles/{cycle_id}/readiness")
def readiness(cycle_id: str, request: Request):
    st = request.app.state.pp
    if cycles.get_cycle(st.db, cycle_id) is None:
        raise HTTPException(404, f"cycle {cycle_id} not found")
    r = corrections.readiness_view(st.db, cycle_id, load_private_policies(st.settings))
    if r is None:
        return _501("payrollpilot_core.readiness.cycle_readiness")
    return {"stage1": r["stage1"], "items": r["items"], "workers": r.get("workers"), "stage2_summary": r.get("stage2_summary")}


def _packet(db, cycle_id: str, policies=None):
    view = cycles.corrected_snapshot(db, cycle_id)
    if view is None:
        raise HTTPException(404, f"cycle {cycle_id} not found")
    corrs = [{k: v for k, v in c.items() if k != "_version"} for c in db.list_records(kinds.CORRECTION, cycle_id=cycle_id)]
    return core_bridge.build_packet(
        snapshot=view, exceptions=cycles.list_exceptions(db, cycle_id), corrections=corrs,
        policies=policies, now=now_iso(),
    )


@router.get("/api/cycles/{cycle_id}/packet")
def packet(cycle_id: str, request: Request):
    if core_bridge.build_packet is None:
        if cycles.get_cycle(request.app.state.pp.db, cycle_id) is None:
            raise HTTPException(404, f"cycle {cycle_id} not found")
        return _501("payrollpilot_core.packet.build_packet")
    st = request.app.state.pp
    return _packet(st.db, cycle_id, load_private_policies(st.settings))


@router.post("/api/cycles/{cycle_id}/workbook")
def workbook(cycle_id: str, request: Request):
    db = request.app.state.pp.db
    if cycles.get_cycle(db, cycle_id) is None:
        raise HTTPException(404, f"cycle {cycle_id} not found")
    if core_bridge.build_packet is None or core_bridge.build_workbook is None:
        return _501("payrollpilot_core.packet.build_packet + workbook.build_workbook")
    st = request.app.state.pp
    pkt = _packet(db, cycle_id, load_private_policies(st.settings))
    wb_id = new_id("wb")
    out_dir = st.settings.private_snapshots_dir.parent / "workbooks"  # data/private/workbooks (gitignored)
    out_dir.mkdir(parents=True, exist_ok=True)
    path: Path = out_dir / f"{cycle_id}_{wb_id}.xlsx"
    try:
        artifact = dict(core_bridge.build_workbook(pkt, str(path)) or {})
    except Exception as exc:
        if type(exc).__name__ != "WorkbookVerificationError":
            raise
        # The workbook did not reopen with matching totals: not a success.
        return JSONResponse(status_code=500, content={"error": "workbook_verification_failed", "detail": str(exc)})
    artifact.setdefault("id", wb_id)
    artifact.setdefault("path", str(path))
    artifact["original_updated"] = False  # never updates the owner's designated workbook in this pilot
    artifact["cycle_id"] = cycle_id
    db.put_record(kinds.WORKBOOK, artifact)
    emit(db, type="workbook.generated", actor="payroll", cycle_id=cycle_id, summary=f"Workbook {artifact['id']} generated",
         refs={"workbook_id": artifact["id"], "sheets": artifact.get("sheets")})
    if artifact.get("verified_totals"):
        emit(db, type="workbook.verified", actor="payroll", cycle_id=cycle_id, summary="Workbook totals verified against packet",
             refs={"workbook_id": artifact["id"]})
    return artifact
