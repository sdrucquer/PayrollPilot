"""Process-wide app state: settings, db, adapters. Created by ``create_app``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .adapters.band import NullBand
from .adapters.memory import InMemoryMemory
from .adapters.messaging import BridgeMessaging, FakeMessaging
from .db import Database
from .settings import Settings


@dataclass
class AppState:
    settings: Settings
    db: Database
    messaging: Any
    memory: Any
    band: Any


def build_state(settings: Settings, db: Database | None = None) -> AppState:
    db = db or Database(settings.db_path)
    messaging = (
        BridgeMessaging(settings.bridge_url, settings.bridge_token)
        if settings.messaging_mode == "bridge"
        else FakeMessaging()
    )
    # Cognee and CLI Band adapters are lane C's; until they land, fall back to labeled dev adapters.
    memory = InMemoryMemory()
    band = NullBand()
    return AppState(settings=settings, db=db, messaging=messaging, memory=memory, band=band)
