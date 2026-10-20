"""Stable, content-derived identifiers (no randomness, no clocks)."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(obj: Any) -> str:
    """sha256 over a canonical JSON encoding, prefixed per CONTRACTS ("sha256:...")."""
    return "sha256:" + hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def exception_id(category: str, entity_refs: dict[str, Any]) -> str:
    """exc_<10 hex> derived from (category, sorted entity refs). Same inputs -> same id."""
    refs = {k: sorted(v) if isinstance(v, list) else v for k, v in entity_refs.items() if v}
    digest = hashlib.sha256(_canonical([category, refs]).encode("utf-8")).hexdigest()
    return f"exc_{digest[:10]}"
