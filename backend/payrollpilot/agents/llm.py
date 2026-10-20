"""OpenRouter chat completions with JSON-schema structured output, usage capture and a hard budget."""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class BudgetExhausted(RuntimeError):
    pass


class LLMUnavailable(RuntimeError):
    pass


@dataclass
class LLMResult:
    data: dict
    usage: dict  # {model, input_tokens, output_tokens, cost_usd}
    duration_ms: int


class Budget:
    def __init__(self, limit_usd: float) -> None:
        self.limit = limit_usd
        self.spent = 0.0
        self._lock = threading.Lock()

    def check(self) -> None:
        if self.spent >= self.limit:
            raise BudgetExhausted(f"model budget ${self.limit:.2f} exhausted (spent ${self.spent:.4f})")

    def add(self, cost: float) -> None:
        with self._lock:
            self.spent += cost or 0.0


_BUDGET = Budget(float(os.environ.get("PP_MODEL_BUDGET_USD", "5.00") or 5.0))


class OpenRouterLLM:
    def __init__(self, model: str | None = None, api_key: str | None = None, budget: Budget | None = None,
                 transport: Callable[[dict, dict], dict] | None = None, timeout_s: float = 45.0) -> None:
        self.model = model or os.environ.get("PP_MODEL", "anthropic/claude-sonnet-5.5")
        self.api_key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        self.budget = budget or _BUDGET
        self.transport = transport  # tests inject recorded responses
        self.timeout_s = timeout_s

    @property
    def available(self) -> bool:
        return bool(self.transport or self.api_key)

    def complete_json(self, system: str, user: str, schema_name: str, schema: dict, max_tokens: int = 800) -> LLMResult:
        if not self.available:
            raise LLMUnavailable("OPENROUTER_API_KEY not set")
        self.budget.check()
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema}},
            "max_tokens": max_tokens,
            "temperature": 0,
            "usage": {"include": True},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "X-Title": "PayrollPilot"}
        t0 = time.time()
        if self.transport:
            resp = self.transport(body, headers)
        else:
            with httpx.Client(timeout=self.timeout_s) as c:
                r = c.post(OPENROUTER_URL, json=body, headers=headers)
            if r.status_code != 200:
                raise LLMUnavailable(f"openrouter {r.status_code}: {r.text[:300]}")
            resp = r.json()
        ms = int((time.time() - t0) * 1000)
        u = resp.get("usage") or {}
        usage = {"model": resp.get("model", self.model), "input_tokens": int(u.get("prompt_tokens", 0)),
                 "output_tokens": int(u.get("completion_tokens", 0)), "cost_usd": float(u.get("cost", 0.0) or 0.0)}
        self.budget.add(usage["cost_usd"])
        content = resp["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(p.get("text", "") for p in content)
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[-1]
        return LLMResult(data=json.loads(text), usage=usage, duration_ms=ms)
