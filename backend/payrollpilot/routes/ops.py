"""Events, approvals, and the run stop flag."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .. import approvals
from ..contracts import ApprovalRequest
from ..events import emit

router = APIRouter()


@router.get("/api/events")
def list_events(request: Request, cycle_id: Optional[str] = None, since: Optional[str] = None, limit: int = 1000):
    return request.app.state.pp.db.list_events(cycle_id=cycle_id, since=since, limit=max(1, min(limit, 5000)))


@router.post("/api/approvals")
def create_approval(body: ApprovalRequest, request: Request):
    db = request.app.state.pp.db
    try:
        return approvals.create_approval(
            db, kind=body.kind, target_id=body.target_id, target_version=body.target_version, scope_text=body.scope_text
        )
    except approvals.ApprovalError as e:
        return JSONResponse(status_code=e.status, content={"error": e.code, "detail": e.detail, **e.extra})


class StopRequest(BaseModel):
    resume: bool = False
    reason: Optional[str] = None


@router.post("/api/run/stop")
def stop(request: Request, body: Optional[StopRequest] = None):
    """Cancels new actions; pending approvals stay pending. ``{"resume": true}`` clears the flag."""
    body = body or StopRequest()
    db = request.app.state.pp.db
    db.set_flag("run_stopped", "0" if body.resume else "1")
    if not body.resume:
        emit(db, type="run.stopped", actor="owner", summary=body.reason or "Owner stopped the run",
             refs={"pending_approvals_kept": True})
    return {"stopped": not body.resume}
