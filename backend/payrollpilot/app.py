"""FastAPI app. Run: ``cd backend && .venv/bin/uvicorn payrollpilot.app:app --port 8000``."""

from __future__ import annotations

import importlib

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .db import Database
from .permissions import PermissionDenied
from .routes import cycles, health, ops, payroll
from .settings import Settings, load_settings
from .state import build_state


def _include_comms(app: FastAPI) -> str:
    """Lane C owns ``payrollpilot/routes_comms.py``. Absent -> "absent"; a
    broken module must not take the whole backend down, so its error is
    reported in /api/health instead of being raised."""
    try:
        routes_comms = importlib.import_module(f"{__package__}.routes_comms")
    except ModuleNotFoundError as exc:
        if exc.name == f"{__package__}.routes_comms":
            return "absent"
        return f"error: {exc!r}"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc!r}"
    app.include_router(routes_comms.router)
    return "loaded"


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
    app.include_router(payroll.router)
    app.state.comms_routes = _include_comms(app)
    return app


app = create_app()
