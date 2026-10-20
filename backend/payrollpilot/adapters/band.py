"""Band adapters. ``NullBand`` only records events (labeled); ``CliBand`` is
lane C's shell adapter in ``payrollpilot/band/`` selected when
``PP_BAND_ENABLED=1``. Business state never lives in Band."""

from __future__ import annotations

from typing import Any


class NullBand:
    mode = "null"
    label = "NULL band (events only, no Band room)"

    def post(self, room: str, text: str, refs: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"posted": False, "mode": self.mode, "room": room}
