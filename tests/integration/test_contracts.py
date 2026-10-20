"""F-01: contract and fixture tests. Catch schema drift between CONTRACTS.md, the shared fixtures,
lane A's pydantic mirror (backend/payrollpilot/contracts.py), the events module and lane B's core output.

Run: backend/.venv/bin/pytest -q tests/integration/test_contracts.py
(backend/.venv has payrollpilot + payrollpilot_core installed editable.)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "docs" / "contracts" / "fixtures"
CONTRACTS_MD = (ROOT / "docs" / "contracts" / "CONTRACTS.md").read_text()
FIXTURE_FILES = ["cycle_synthetic_v1.json", "expected_exceptions_v1.json", "quote_pool_cases.json",
                 "replies_v1.json", "readiness_matrix_v1.json"]
DENYLIST = ROOT / "data" / "private" / "denylist.txt"

E164 = re.compile(r"\+\d{10,15}\b")
SPACED_US_PHONE = re.compile(r"\+?1?[\s.-]?\(?(\d{3})\)?[\s.-]\d{3}[\s.-]\d{4}\b")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
FICTIONAL_555 = re.compile(r"\b555\b")  # 555 area code or exchange: fictional


def load(name: str):
    return json.loads((FIX / name).read_text())


def walk(obj, path=""):
    """Yield (path, key, value) for every dict entry, recursively."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path, k, v
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


# ------------------------------------------------------------------ files load
@pytest.mark.parametrize("name", FIXTURE_FILES)
def test_fixture_loads(name):
    assert load(name)


# ------------------------------------------------------------------ units
def _int_or_null(v):
    return v is None or (isinstance(v, int) and not isinstance(v, bool))


@pytest.mark.parametrize("name", FIXTURE_FILES)
def test_money_fields_are_int_cents_or_null(name):
    bad = []
    for path, k, v in walk(load(name)):
        if k.endswith("_cents"):
            vals = v.values() if isinstance(v, dict) else [v]  # {worker_id: cents} maps are allowed
            if not all(_int_or_null(x) for x in vals):
                bad.append(f"{path}.{k}={v!r}")
        if k in ("amount", "price", "total", "rate", "gross", "balance"):
            bad.append(f"{path}.{k}: money key without _cents suffix")
        if isinstance(v, float) and ("cents" in k or "amount" in k):
            bad.append(f"{path}.{k} is a float")
    assert not bad, bad


@pytest.mark.parametrize("name", FIXTURE_FILES)
def test_duration_fields_are_int_minutes_or_null(name):
    bad = [f"{p}.{k}={v!r}" for p, k, v in walk(load(name))
           if k.endswith("_minutes") and not isinstance(v, dict) and not _int_or_null(v)]
    bad += [f"{p}.{k}" for p, k, v in walk(load(name)) if k in ("hours", "duration") and v is not None]
    assert not bad, bad


# ------------------------------------------------------------------ provenance
PROVENANCE = {"real", "cached", "synthetic", "seeded_issue", "test_reply"}


def test_every_snapshot_record_with_contract_provenance_has_it():
    snap = load("cycle_synthetic_v1.json")
    assert snap["provenance"] in PROVENANCE and snap["cycle"]["provenance"] in ("real", "synthetic")
    missing = []
    for coll in ("workers", "jobs", "time_entries", "costs", "obligations"):
        for rec in snap[coll]:
            if rec.get("provenance") not in PROVENANCE:
                missing.append(f"{coll}/{rec['id']}")
    assert not missing, missing


def test_fixture_provenance_is_never_real():
    for name in FIXTURE_FILES:
        for _, k, v in walk(load(name)):
            if k == "provenance":
                assert v != "real", name


@pytest.mark.xfail(strict=False, reason="CONTRACTS v1.1 Receipt has no provenance field (AGENTS.md says every record "
                                        "carries provenance). Lead decision requested; see F-01 PR.")
def test_receipts_carry_provenance():
    assert all("provenance" in r for r in load("cycle_synthetic_v1.json")["receipts"])


# ------------------------------------------------------------------ pydantic mirror validates fixtures
def test_snapshot_validates_against_backend_contract_models():
    from payrollpilot import contracts as C

    snap = load("cycle_synthetic_v1.json")
    C.PayrollCycle.model_validate(snap["cycle"])
    for w in snap["workers"]:
        C.Worker.model_validate(w)
    for t in snap["time_entries"]:
        C.TimeEntry.model_validate(t)
    for j in snap["jobs"]:
        C.Job.model_validate(j)
    for r in snap["receipts"]:
        C.Receipt.model_validate(r)
    for c in snap["costs"]:
        C.EconomicCost.model_validate(c)
    for o in snap["obligations"]:
        C.Obligation.model_validate(o)


def test_cost_allocations_reconcile_when_allocated():
    for c in load("cycle_synthetic_v1.json")["costs"]:
        if c["allocated"] and c["amount_cents"] is not None and c["job_allocations"]:
            assert sum(a["amount_cents"] for a in c["job_allocations"]) == c["amount_cents"], c["id"]


def test_ids_use_contract_prefixes():
    snap = load("cycle_synthetic_v1.json")
    prefixes = {"workers": "wkr_", "jobs": "job_", "time_entries": "te_", "receipts": "rcpt_", "costs": "cost_",
                "obligations": "obl_"}
    for coll, pre in prefixes.items():
        assert all(r["id"].startswith(pre) for r in snap[coll]), coll
    assert snap["cycle"]["id"].startswith("cyc_")
    ids = [r["id"] for coll in prefixes for r in snap[coll]]
    assert len(ids) == len(set(ids))


# ------------------------------------------------------------------ exceptions: states, categories, core output
def _md_enum_starting(field: str, first: str) -> set[str]:
    """The CONTRACTS.md enum for `field` whose first value is `first` (several fields share a name)."""
    m = re.search(rf'"{field}":\s*("{first}"(?:\s*\|\s*"[a-z_.]+")+)', CONTRACTS_MD)
    assert m, (field, first)
    return set(re.findall(r'"([a-z_.]+)"', m.group(1)))


def test_exception_enums_match_between_contracts_md_and_backend_models():
    from typing import get_args

    from payrollpilot import contracts as C

    assert _md_enum_starting("state", "detected") == set(get_args(C.ExceptionState))
    assert _md_enum_starting("category", "missing_job") == set(get_args(C.ExceptionCategory))


def test_expected_exceptions_and_core_audit_conform():
    from typing import get_args

    from payrollpilot import contracts as C
    from payrollpilot_core.audit import run_audit

    exp = load("expected_exceptions_v1.json")
    cats = set(get_args(C.ExceptionCategory))
    assert all(e["category"] in cats for e in exp["exceptions"])
    got = run_audit(load("cycle_synthetic_v1.json"))
    assert {e["id"] for e in got} == {e["id"] for e in exp["exceptions"]}
    for e in got:
        C.PayrollException.model_validate(e)
        assert e["state"] in set(get_args(C.ExceptionState))


def test_core_readiness_and_items_validate_against_models():
    from payrollpilot import contracts as C
    from payrollpilot_core.audit import run_audit
    from payrollpilot_core.readiness import cycle_readiness

    snap = load("cycle_synthetic_v1.json")
    out = cycle_readiness(snap, run_audit(snap))
    C.Readiness.model_validate(out["stage1"])
    for item in out["items"]:
        C.CompensationItem.model_validate(item)
    matrix = load("readiness_matrix_v1.json")
    for phase in ("before", "after_t02_correction"):
        for r in list(matrix[phase]["items"].values()) + list(matrix[phase]["workers"].values()):
            C.Readiness.model_validate(r)


# ------------------------------------------------------------------ events
def test_event_types_match_contracts_md():
    from payrollpilot.events import ACTORS, EVENT_TYPES

    section = CONTRACTS_MD.split("## 4. Events", 1)[1].split("## 5.", 1)[0]
    types_line = section.split("Types:", 1)[1]
    md_types = set(re.findall(r"`([a-z_]+\.[a-z_]+)`", types_line))
    assert md_types == set(EVENT_TYPES)
    md_actors = set(re.findall(r'"([a-z]+)"', section.split('"actor":', 1)[1].split(",", 1)[0]))
    assert md_actors == set(ACTORS)


# ------------------------------------------------------------------ replies fixture
def test_replies_cover_required_scenarios_and_resolve_placeholders():
    replies = load("replies_v1.json")["replies"]
    cats = {e["category"] for e in load("expected_exceptions_v1.json")["exceptions"]}
    names = " ".join(r["name"] for r in replies)
    for needle in ("clean", "T14", "conflicting", "T17"):
        assert needle in names
    for r in replies:
        for ph in r["batch_exception_ids"]:
            assert ph.strip("{}") in cats, ph
    t17 = next(r for r in replies if "T17" in r["name"])
    assert t17["expect"]["blocked_event"] == "blocked.unauthorized_instruction"


# ------------------------------------------------------------------ privacy
@pytest.mark.parametrize("name", FIXTURE_FILES)
def test_no_phone_or_email_keys_or_values(name):
    doc = load(name)
    bad = [f"{p}.{k}" for p, k, _ in walk(doc) if "phone" in k.lower() or "@" in k or "email" in k.lower()]
    for s in strings(doc):
        if EMAIL.search(s):
            bad.append(f"email-like: {s[:60]}")
        if E164.search(s):
            bad.append(f"E.164: {s[:60]}")
        for m in SPACED_US_PHONE.finditer(s):
            if not FICTIONAL_555.search(m.group(0)):
                bad.append(f"phone-like: {s[:60]}")
    assert not bad, bad


def test_display_names_are_deidentified():
    snap = load("cycle_synthetic_v1.json")
    assert {w["display_name"] for w in snap["workers"]} <= {f"Worker {c}" for c in "ABCDEFGH"}
    assert snap["cycle"]["company_label"] == "Pilot Co"
    assert all(re.fullmatch(r"Job \d\d \(.+\)", j["display_name"]) for j in snap["jobs"])


def test_manager_split_is_placeholder_and_not_the_private_allocation():
    split = load("cycle_synthetic_v1.json")["policies"]["manager_split"]
    assert split["status"] == "placeholder"
    assert split["split_percent"] != {"retained": 50, "mgr_a": 10, "mgr_b": 20, "owner": 20}


@pytest.mark.skipif(not DENYLIST.exists(), reason="data/private/denylist.txt not present (private, lead-supplied)")
@pytest.mark.parametrize("name", FIXTURE_FILES)
def test_no_denylisted_terms(name):
    terms = [t.strip().lower() for t in DENYLIST.read_text().splitlines() if t.strip() and not t.startswith("#")]
    text = (FIX / name).read_text().lower()
    hits = [t for t in terms if re.search(rf"\b{re.escape(t)}\b", text)]
    assert not hits, f"{name}: {len(hits)} denylisted term(s)"  # never print the terms themselves
