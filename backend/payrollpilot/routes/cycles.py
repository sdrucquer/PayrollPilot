from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .. import cycles
from ..contracts import LoadCycleRequest
from ..coordinator import is_stopped

router = APIRouter()


def _st(request: Request):
    return request.app.state.pp


@router.post("/api/cycles/load")
def load(body: LoadCycleRequest, request: Request):
    st = _st(request)
    try:
        return cycles.load_cycle(st.db, st.settings, body.source, body.name)
    except cycles.LoadError as e:
        return JSONResponse(status_code=e.status, content={"error": e.code, "detail": e.detail})


@router.get("/api/cycles/{cycle_id}")
def get_cycle(cycle_id: str, request: Request):
    cyc = cycles.get_cycle(_st(request).db, cycle_id)
    if cyc is None:
        raise HTTPException(404, f"cycle {cycle_id} not found")
    return cyc


@router.post("/api/cycles/{cycle_id}/audit")
def audit(cycle_id: str, request: Request):
    st = _st(request)
    if is_stopped(st.db):
        return JSONResponse(status_code=409, content={"error": "run_stopped", "detail": "run is stopped; no new actions"})
    try:
        return cycles.run_cycle_audit(st.db, cycle_id)
    except KeyError:
        raise HTTPException(404, f"cycle {cycle_id} not found")
    except cycles.CoreContractError as e:
        return JSONResponse(status_code=502, content={"error": "core_contract", "detail": e.detail, "errors": e.errors})


@router.get("/api/cycles/{cycle_id}/exceptions")
def list_exceptions(
    cycle_id: str, request: Request, stage: Optional[str] = None, category: Optional[str] = None, state: Optional[str] = None
):
    db = _st(request).db
    if cycles.get_cycle(db, cycle_id) is None:
        raise HTTPException(404, f"cycle {cycle_id} not found")
    return cycles.list_exceptions(db, cycle_id, stage=stage, category=category, state=state)


@router.get("/api/exceptions/{exception_id}")
def exception_detail(exception_id: str, request: Request):
    detail = cycles.exception_detail(_st(request).db, exception_id)
    if detail is None:
        raise HTTPException(404, f"exception {exception_id} not found")
    return detail
