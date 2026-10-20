"""Deterministic T17 guard. Inbound text is data: anything that reads like an instruction to pay, transfer,
change recipients, or override the workflow is blocked in code before any model sees it."""
from __future__ import annotations

import re

_PATTERNS = [
    (r"\b(pay|send|transfer|wire|venmo|zelle|bonus|reimburse)\b[^.]*\$\s?\d", "payment_instruction"),
    (r"\$\s?\d[\d,]*(\.\d+)?\s*(bonus|now|today)", "payment_instruction"),
    (r"\bignore (the|all|previous|your)\b", "override_instruction"),
    (r"\b(send|forward|text|email)\b[^.]*\b(to|at)\b[^.]*(\+?\d[\d\s().-]{8,}\d|@[\w.-]+\.\w+)", "new_recipient"),
    (r"\bsubmit (the )?payroll\b|\brun payroll\b", "payroll_submit"),
    (r"\b(change|update|edit)\b[^.]*\b(rate|bank|account|routing)\b", "source_change"),
]
_PHONE = re.compile(r"\+?\d[\d\s().-]{8,}\d")


def unauthorized_instruction(text: str) -> list[str]:
    t = text.lower()
    hits = [code for pat, code in _PATTERNS if re.search(pat, t)]
    return sorted(set(hits))


def redact(text: str) -> str:
    """Strip phone-like numbers before storing/sending text to a model."""
    return _PHONE.sub("[number removed]", text)


_VAGUE = re.compile(r"^\s*(yes|yep|yeah|ok|okay|sure|correct|right|no|nope|y|n|k|👍)[\s.!]*$", re.I)


def is_vague(text: str) -> bool:
    return bool(_VAGUE.match(text))
