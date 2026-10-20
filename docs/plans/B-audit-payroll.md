# Lane B: Audit rules and payroll calculation

Owner: Claude Code session "B". Branch `lane/b-core`, worktree `../PayrollPilot-b`. Binding: shared context, CONTRACTS, AGENTS.
Owns: `core/` (`core/pyproject.toml`, `core/payrollpilot_core/`, `core/tests/`), `docs/contracts/fixtures/*.json`, `data/fixtures/`. Must not edit: `backend/`, `web/`, `bridge/`, other plans. Needs nothing from other lanes to start.
Mission: pure, tested Python for everything that touches money, time, readiness, and the workbook. No IO, no LLM. Lane A calls you; lane D renders your output; lane F tests you.

## Tasks

### B-01 Fixtures + package + duration/time normalization (P0) — 25 min — start now
- Deps: none.
- Steps: `core/pyproject.toml` (name `payrollpilot-core`, deps: openpyxl; dev: pytest). Write `docs/contracts/fixtures/cycle_synthetic_v1.json`, `expected_exceptions_v1.json`, `quote_pool_cases.json`, `replies_v1.json`, `readiness_matrix_v1.json` exactly as CONTRACTS section 6 describes (all `provenance: synthetic`/`seeded_issue`; names `Worker A..D`, `Job 01..03`, `Pilot Co`; no real rates: use 2200, 2500, 3000 cents/hour placeholders; the manager split fixture uses placeholder `{"retained": 50, "mgr_a": 10, "mgr_b": 20, "owner": 20}` with a comment that real named assignments live in the private policy file). `time.py`: `normalize_duration`, `weekly_minutes`, overlap/duplicate detection helpers. `money.py`: `cents`, `gross_wages` (Decimal, round half-even once).
- Acceptance (T01, T05): `"2h14"` -> 134; weekly totals are per fixed workweek, never averaged; invalid durations raise.
- Verify: `cd core && python3 -m venv .venv && .venv/bin/pip install -e .[dev] && .venv/bin/pytest -q tests/test_time.py tests/test_money.py` -> all pass. Also `python3 -I -c "import json;json.load(open('docs/contracts/fixtures/cycle_synthetic_v1.json'))"`.
- Handoff: push fixtures first (even before tests) so A, D, F can consume them. Tell the lead the fixture is up.

### B-02 Deterministic audit rules (P0) — 30 min
- Deps: B-01.
- `audit.py`: `run_audit(snapshot: dict) -> list[dict]` producing CONTRACTS `Exception` dicts for: missing_job, long_shift (>8h, review only), open_timer, overlap, duplicate_time, unassigned_time, schedule_mismatch, identity (duplicate/inactive profiles), rate_unconfirmed, already_paid_allocation (paid entry whose job is questioned -> `stage_impact.stage1_wages: none`, `stage2_costs: job_costing`), unmatched_cost, cost_conflict (amount mismatch across representations), offsite_link, coverage_gap (any `SourceCoverage.complete == false`), approval-queue trap (entries outside cycle bounds are excluded and reported, never swept in: T27). Each exception: stable id derived from a hash of (category, entity refs), evidence refs, `dollars_affected_cents` null when unknown, `intended_respondent_role` per PRD section 5 (facts -> ops_lead; rate/policy -> owner).
- Acceptance (FR-04, FR-05, FR-06, FR-07, T02, T03, T07, T13, T23, T27): output matches `expected_exceptions_v1.json` set-wise; running twice yields identical ids; no exception trims hours or assumes breaks.
- Verify: `core/.venv/bin/pytest -q tests/test_audit.py`.
- Handoff: A wires `POST /audit`; F runs the expected-exceptions contract test.

### B-03 Compensation calc + readiness (P0) — 30 min
- Deps: B-01. Parallel with B-02 if you split work across two files.
- `calc.py`: `quote_pool` (T10: 100000 -> 5000 -> 2500/2500; deposit-only ineligible; null profit, >2 quoters, profit<=0 -> `PolicyMissing` with code), `cycle_profit_bridge` (each component once; null -> result null + blocker), `labor_revenue_ratios` (zero/negative denominator -> `not_meaningful`), `manager_pool` (reads split percentages from a passed-in policy dict; refuses when pool null/negative or any `requires_resolution` flag; never from constants in code), obligations: `apply_settlement(obligation, settlement)` reduces balance, never creates earnings (T21).
- `readiness.py`: `readiness_for(item, exceptions, policies) -> Readiness` per PRD 11.3; `stage1_readiness(workers, exceptions)` partial-by-worker; blockers carry codes `policy_missing:<O-id>`, `exception:<exc_id>`, `coverage:<dataset>`. Rule: a manager-pool blocker never appears on a commission card; a commission blocker never invalidates wages (T09, T24).
- Acceptance (FR-16 to FR-21, FR-27, T09, T10, T11, T12, T19, T21, T22, T24, T26): all cases in `quote_pool_cases.json` and `readiness_matrix_v1.json` pass.
- Verify: `core/.venv/bin/pytest -q tests/test_calc.py tests/test_readiness.py`.
- Handoff: A wires readiness/packet routes; D renders `Readiness`.

### B-04 Packet + workbook builder (P0) — 25 min
- Deps: B-02, B-03.
- `packet.py`: `build_packet(cycle, workers, entries, items, exceptions, corrections) -> dict` (period, identities as display names, earnings categories, calc version `calc_v1`, evidence refs, scoped readiness, workbook ref placeholder). `workbook.py`: `build_workbook(packet, path) -> WorkbookArtifact`; 12 ledgers + Sources sheet; pending tabs have header + `status: pending — <blocker>`; reopen with openpyxl and assert `Review` totals equal packet totals; `original_updated: false`, `note: "Provisional review workbook; designated workbook not supplied/updated."`
- Acceptance (FR-22, FR-28, T28): all 12 sheets present; totals verified; no real names.
- Verify: `core/.venv/bin/pytest -q tests/test_workbook.py`; open the xlsx once manually and screenshot (E needs it).
- Handoff: A wires the route; E uses the screenshot.

### B-05 Local correction impact (P0, small) — 15 min
- `corrections.py`: `propose_correction(kind, before, after, snapshot) -> LocalCorrection` with `calculation_impact` computed by re-running calc on a corrected view (pure). T02: wages delta 0, job labor delta != 0. T20: a time confirmation reconciles the whole affected workweek, not new hours × rate; if prior payroll for that week is unknown -> blocker `prior_recognition_unknown`.

## Status log

```
LANE B status @ 12:40
Done: B-01 (acceptance checks passed: T01 "2h14" -> 134; T05 weekly totals per fixed workweek, never averaged; invalid durations raise; null stays null)
Changed files: core/pyproject.toml, core/payrollpilot_core/{__init__,ids,money,time}.py, core/tests/test_{time,money}.py, core/tools/build_fixtures.py, docs/contracts/fixtures/*.json (5)
Tests run: core/.venv/bin/pytest -q tests/test_time.py tests/test_money.py -> 35 passed
Evidence: fixtures pushed 12:39 (fd57ea2); all 5 parse with python3 -I json.load
Blockers: none. Lead decision requested: bless fixture extensions TimeEntry.scheduled_job_id, snapshot.policies, snapshot.obligations, Exception.entity_refs.coverage
Next: B-02 audit, B-03 calc/readiness
Handoff requested: A, D, F consume docs/contracts/fixtures/*.json (cycle id cyc_synth_v1)
```
