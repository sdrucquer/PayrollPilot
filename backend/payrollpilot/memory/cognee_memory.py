"""Real Cognee adapter (local SQLite + LanceDB + Kuzu; embeddings fastembed; LLM via OpenRouter)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .base import DATASET, MARKER, MemoryHit, memory_text_for_resolution, parse_refs

BACKEND_DIR = Path(__file__).resolve().parents[2]
_configured = False


def configure() -> None:
    """Load backend/.env, apply local defaults, and pin Cognee storage under backend/ (gitignored)."""
    global _configured
    if _configured:
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND_DIR / ".env")
    except ImportError:
        pass
    os.environ.setdefault("EMBEDDING_PROVIDER", "fastembed")
    os.environ.setdefault("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    os.environ.setdefault("EMBEDDING_DIMENSIONS", "384")
    os.environ.setdefault("LLM_PROVIDER", "custom")
    os.environ.setdefault("LLM_ENDPOINT", "https://openrouter.ai/api/v1")
    os.environ.setdefault("LLM_MODEL", "openrouter/anthropic/claude-haiku-5.5")
    if not os.environ.get("LLM_API_KEY") and os.environ.get("OPENROUTER_API_KEY"):
        os.environ["LLM_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
    os.environ.setdefault("TELEMETRY_DISABLED", "1")
    import cognee

    cognee.config.system_root_directory(str(BACKEND_DIR / ".cognee_system"))
    cognee.config.data_root_directory(str(BACKEND_DIR / ".cognee_data"))
    _configured = True


def _texts(obj: Any) -> list[str]:
    """Collect every string in a Cognee result structure that carries our marker."""
    out: list[str] = []

    def walk(o: Any) -> None:
        if isinstance(o, str):
            if MARKER in o:
                out.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, (list, tuple, set)):
            for v in o:
                walk(v)
        elif hasattr(o, "model_dump"):
            walk(o.model_dump())
        elif hasattr(o, "__dict__"):
            walk(vars(o))

    walk(obj)
    return list(dict.fromkeys(out))


class CogneeMemory:
    name = "cognee"

    def __init__(self, dataset: str = DATASET, search_type: str | None = None) -> None:
        configure()
        self.dataset = dataset
        self.search_type = search_type or os.environ.get("PP_COGNEE_SEARCH", "CHUNKS")

    async def write_resolution(self, resolution: dict) -> str:
        import cognee

        text = memory_text_for_resolution(resolution)
        result = await cognee.remember(text, dataset_name=self.dataset)
        return f"mem_{resolution['id']}"  # memory_ref back to the res_ id; Cognee ids stay internal

    async def recall(self, query: str, scope: dict) -> list[MemoryHit]:
        import cognee
        from cognee import SearchType

        qt = getattr(SearchType, self.search_type)
        results = await cognee.recall(query, query_type=qt, datasets=[self.dataset], top_k=5)
        hits = []
        for t in _texts(results):
            # A chunk may hold several sentences; split on our marker to keep one resolution per hit.
            for piece in [p for p in t.split(MARKER) if p.strip()]:
                piece = MARKER + piece if not piece.startswith(MARKER) else piece
                hits.append(MemoryHit(text=piece.strip(), refs=parse_refs(piece), source="cognee", raw=None))
        return hits


def raw_dump(results: Any) -> str:
    try:
        return json.dumps(results, default=lambda o: getattr(o, "model_dump", lambda: str(o))(), indent=1)[:4000]
    except Exception:
        return repr(results)[:4000]
