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

```
LANE B status @ 12:43
Done: B-02 (acceptance checks passed: output equals expected_exceptions_v1 set-wise and by id/stage_impact/respondent; identical ids on rerun; no trimming or assumed breaks (input unchanged); T02 allocation-only with stage1 none; T03 long shift flagged; T07 shared cost reconciles, mismatch -> cost_conflict; T13 coverage gap; T23 bank+Jobber same cost counted once; T27 out-of-cycle entries excluded and reported, both boundaries)
Changed files: core/payrollpilot_core/audit.py, core/tests/test_audit.py
Tests run: core/.venv/bin/pytest -q tests/test_audit.py -> 16 passed; full core suite -> 51 passed
Evidence: run_audit(cycle_synthetic_v1) -> 15 exceptions with stable ids exc_<10hex>
Blockers: none. Open decision: out-of-cycle entries (T27) use category unassigned_time (no dedicated category in CONTRACTS); respondent owner.
Next: B-03 calc + readiness
Handoff requested: A wires POST /api/cycles/{id}/audit -> payrollpilot_core.audit.run_audit(snapshot, now=None); F runs expected-exceptions contract test
```

```
LANE B status @ 12:48
Done: B-03 (acceptance checks passed: all 11 quote_pool_cases incl. T10 100000 -> 5000 -> 2500/2500, deposit-only ineligible, null/zero/negative profit and 3 quoters -> PolicyMissing; readiness_matrix_v1 before and after the T02 correction match on state, unknown_amount and blocker codes; T09 cost/commission blockers never reach wage cards; T11 no default marketing/overhead/tip policy; T12 tip excluded from receipts and pending; T19 proposed or approved allocation does not exclude collection-cycle revenue, only finalized+evidence does; T21 settlement reduces balance, never new earnings, unknown recognition blocks; T22 ratios separate, no threshold, zero/negative/unknown denominator not meaningful; T24 commission can be ready while manager pool blocked, manager blockers never on commission cards; T26 split comes only from the policy dict)
Changed files: core/payrollpilot_core/{calc,readiness}.py, core/tests/test_{calc,readiness}.py, core/tools/build_fixtures.py, docs/contracts/fixtures/readiness_matrix_v1.json
Tests run: core/.venv/bin/pytest -q -> 87 passed (test_calc + test_readiness: 37)
Evidence: cycle_readiness(cycle_synthetic_v1) -> stage1 partial (1 of 4 workers), quote job_01 pending, quote job_02 not_meaningful, marketing pending, tip pending, manager pool blocked
Blockers: none. Fixture change: readiness_matrix_v1.json is stricter than the 12:39 version (job_01 quote also blocked by unassigned labor, overlap, unverified labor rate and identity; manager pool also blocked by every open cost-affecting exception and commissions_pending; Worker D unknown_amount true). Consumers (D, F) should re-pull.
Next: B-05 corrections, then B-04 packet + workbook
Handoff requested: A wires GET /api/cycles/{id}/readiness -> payrollpilot_core.readiness.cycle_readiness(snapshot, exceptions, policies=<private policy file or None>) and returns {stage1, items}; D renders Readiness
```

```
LANE B status @ 12:50
Done: B-05 (acceptance checks passed: T02 job_allocation te_0014 job_01 -> job_02 gives stage1_wages_delta_cents 0 and job labor -20000/+20000, equal to readiness_matrix_v1; applied view reproduces the after-correction readiness; source snapshot untouched; T20 time confirmation reconciles the whole workweek against prior recognized payroll, unknown prior -> prior_recognition_unknown and delta null (not new hours x rate), known prior -> week gross minus prior; stale before refused; identity_merge explicitly unsupported; paid entries -> paid_adjustment_decision; cost_link allocations must reconcile)
Changed files: core/payrollpilot_core/corrections.py, core/tests/test_corrections.py
Tests run: core/.venv/bin/pytest -q -> 99 passed (test_corrections: 11)
Evidence: propose_correction(job_allocation, T02) -> calculation_impact {stage1_wages_delta_cents: 0, job_costing_delta: [job_01 -20000, job_02 +20000]}
Blockers: none. Open decision: weeks over 40h raise policy_missing:O02_overtime instead of computing overtime.
Next: B-04 packet + workbook
Handoff requested: A calls propose_correction(kind, before, after, view) -> LocalCorrection with calculation_impact, blockers and target_version; apply_corrections(snapshot, corrections) mirrors corrected_snapshot
```

```
LANE B status @ 12:55
Done: B-04 (acceptance checks passed: T28 all 12 ledgers plus Sources present; workbook reopened and Review totals plus draft version equal the packet; tampered total fails verification; pending tabs (Overhead, Quotes & marketing, Tips, Manual payments, Carry-forward) have header plus 'status: pending — <blocker>' row; original_updated false with the provisional note; no real names, @ or phone numbers; FR-22 packet has period, display-name identities, earnings, calc_v1, evidence, scoped readiness, workbook_ref placeholder; unknown totals stay unknown, never 0)
Changed files: core/payrollpilot_core/{packet,workbook}.py, core/tests/test_workbook.py, data/fixtures/review_workbook_synthetic_v1.xlsx, data/fixtures/review_workbook_synthetic_v1_review.png
Tests run: core/.venv/bin/pytest -q -> 106 passed (test_workbook: 7)
Evidence: data/fixtures/review_workbook_synthetic_v1.xlsx (draft_c8074d1db110, verified) and its Review-sheet screenshot data/fixtures/review_workbook_synthetic_v1_review.png (macOS Quick Look render) for lane E
Blockers: none. Sheet named 'Quotes & marketing' because Excel forbids '/' in sheet names.
Next: none in plan; available for fixes and integration
Handoff requested: A calls build_packet(snapshot=view, exceptions=excs, corrections=corrs, policies=private_or_None, now=ts) then build_workbook(packet, path) -> WorkbookArtifact; the legacy positional form works but reports receipts, costs and jobs as not supplied. E uses the screenshot.
```
