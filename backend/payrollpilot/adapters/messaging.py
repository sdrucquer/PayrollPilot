"""Messaging adapters. ``FakeMessaging`` is for local development only and is
labeled as such in ``/api/health``; ``BridgeMessaging`` talks to the Bun bridge
(lane C) which talks to Photon. Neither contains business logic. Lane C may
extend ``BridgeMessaging`` (send payload, inbound forwarding)."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

import httpx


class Messaging(Protocol):
    mode: str
    label: str

    def send(self, batch: dict[str, Any]) -> dict[str, Any]: ...


class FakeMessaging:
    mode = "fake"
    label = "FAKE messaging (dev only, nothing is sent)"

    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    def send(self, batch: dict[str, Any]) -> dict[str, Any]:
        pmid = f"fake_{uuid.uuid4().hex[:10]}"
        self.sent.append({"batch_id": batch["id"], "provider_message_id": pmid})
        return {"provider_message_id": pmid, "status": "sent", "provenance": "fake"}


class BridgeMessaging:
    mode = "bridge"
    label = "Bridge -> Photon iMessage"

    def __init__(self, base_url: str, token: str, timeout_s: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_s = timeout_s

    def send(self, batch: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "batch_id": batch["id"],
            "recipient": batch["actual_recipient"],
            "text": batch["text"],
            "text_hash": batch.get("text_hash"),
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(f"{self.base_url}/send", json=payload, headers={"X-PP-Bridge-Token": self.token})
        resp.raise_for_status()
        return resp.json()
