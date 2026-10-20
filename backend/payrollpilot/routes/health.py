from __future__ import annotations

from fastapi import APIRouter, Request

from .. import CONTRACT_VERSION
from .. import core_bridge

router = APIRouter()


@router.get("/api/health")
def health(request: Request) -> dict:
    st = request.app.state.pp
    s = st.settings
    # Integration status values are tested|unverified|blocked. Nothing is
    # "tested" until a lane records real evidence in INTEGRATION-FINDINGS.md.
    return {
        "ok": True,
        "contract_version": CONTRACT_VERSION,
        "integrations": {
            "photon": "unverified",
            "band": "unverified",
            "cognee": "unverified",
            "browser_use": "unverified" if s.browser_use_key_present else "blocked",
        },
        "adapters": {
            "messaging": {"mode": st.messaging.mode, "label": st.messaging.label},
            "memory": {"mode": st.memory.mode, "label": st.memory.label},
            "band": {"mode": st.band.mode, "label": st.band.label},
            "audit": core_bridge.AUDIT_MODE,
        },
        "test_recipient_configured": bool(s.test_recipient),
        "run_stopped": st.db.get_flag("run_stopped") == "1",
    }
