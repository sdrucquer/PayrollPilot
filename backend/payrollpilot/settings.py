"""Environment-backed settings. Values come from ``backend/.env`` (gitignored)
or the process environment; ``.env.example`` at the repo root lists the names.

Nothing here is a financial policy. Adapter selection is reversible by env.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

# Load backend/.env once; real env vars win over file values.
load_dotenv(BACKEND_DIR / ".env", override=False)


def _env(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    return default if value is None or value == "" else value


@dataclass(frozen=True)
class Settings:
    db_path: Path
    fixtures_dir: Path
    private_snapshots_dir: Path
    test_recipient: str
    intended_respondent_label: str
    bridge_token: str
    bridge_url: str
    messaging_mode: str  # "fake" | "bridge"
    memory_mode: str  # "inmemory" | "cognee"
    band_mode: str  # "null" | "cli"
    band_room: str
    browser_use_key_present: bool
    company_label: str
    business_tz: str
    allowlist: tuple[str, ...] = field(default_factory=tuple)


def load_settings() -> Settings:
    recipient = _env("PP_TEST_RECIPIENT").strip()
    allowlist = (recipient,) if recipient else ()
    messaging_mode = _env("PP_MESSAGING", "fake").lower()
    memory_mode = _env("PP_MEMORY", "inmemory").lower()
    band_mode = "cli" if _env("PP_BAND_ENABLED", "0") == "1" else "null"
    return Settings(
        db_path=Path(_env("PP_DB_PATH", str(BACKEND_DIR / "data" / "payrollpilot.db"))),
        fixtures_dir=Path(_env("PP_FIXTURES_DIR", str(REPO_ROOT / "docs" / "contracts" / "fixtures"))),
        private_snapshots_dir=Path(
            _env("PP_PRIVATE_SNAPSHOTS_DIR", str(REPO_ROOT / "data" / "private" / "snapshots"))
        ),
        test_recipient=recipient,
        intended_respondent_label=_env("PP_INTENDED_RESPONDENT_LABEL", "Operations lead"),
        bridge_token=_env("PP_BRIDGE_TOKEN", "change-me"),
        bridge_url=_env("PP_BRIDGE_URL", "http://127.0.0.1:3001"),
        messaging_mode=messaging_mode if messaging_mode in {"fake", "bridge"} else "fake",
        memory_mode=memory_mode if memory_mode in {"inmemory", "cognee"} else "inmemory",
        band_mode=band_mode,
        band_room=_env("PP_BAND_ROOM", "PayrollPilot Cases"),
        browser_use_key_present=bool(_env("BROWSER_USE_API_KEY")),
        company_label=_env("PP_COMPANY_LABEL", "Pilot Co"),
        business_tz=_env("PP_BUSINESS_TZ", "America/New_York"),
        allowlist=allowlist,
    )


def mask_handle(handle: str) -> str:
    """Mask a phone/handle for display: keep the last two characters only."""
    if not handle:
        return ""
    tail = handle[-2:]
    return f"***-**{tail}"
