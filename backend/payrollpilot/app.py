"""FastAPI app. Run: ``cd backend && .venv/bin/uvicorn payrollpilot.app:app --port 8000``."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .db import Database
from .permissions import PermissionDenied
from .routes import cycles, health, ops
from .settings import Settings, load_settings
from .state import build_state


def create_app(settings: Settings | None = None, db: Database | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="PayrollPilot backend", version="0.1.0")
    app.state.pp = build_state(settings, db)

    @app.exception_handler(PermissionDenied)
    async def _denied(_: Request, exc: PermissionDenied) -> JSONResponse:
        return JSONResponse(status_code=403, content={"error": exc.code, "detail": exc.detail})

    @app.exception_handler(NotImplementedError)
    async def _gated(_: Request, exc: NotImplementedError) -> JSONResponse:
        return JSONResponse(status_code=501, content={"error": "gated", "detail": str(exc)})

    app.include_router(health.router)
    app.include_router(cycles.router)
    app.include_router(ops.router)
    return app


app = create_app()
