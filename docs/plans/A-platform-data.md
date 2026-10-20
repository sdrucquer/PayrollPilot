# Lane A: Platform and data

Owner: Claude Code session "A". Branch `lane/a-platform`, worktree `../PayrollPilot-a`. Binding: `docs/plans/00-shared-context.md`, `docs/contracts/CONTRACTS.md`, `AGENTS.md`.
Owns: `backend/` (except `backend/payrollpilot/agents/`, `memory/`, `band/`, messaging routes which are lane C), `scripts/`, `data/private/`, `backend/payrollpilot/contracts.py` (first PR only; afterwards lead). Must not edit: `core/`, `bridge/`, `web/`, `demo/`, other plans.
Mission: a running FastAPI backend that loads a cycle (fixture or private snapshot), runs lane B's audit, stores exceptions/approvals/corrections/events durably, and exposes every route in CONTRACTS section 5 that is not lane C's. Plus one authorized real Jobber read via Browser Use, timeboxed.

## Tasks

### A-01 Scaffold + persistence + health (P0) — 25 min — start now
- Deps: none. Safe before anything: everything.
- Steps: `backend/pyproject.toml` (or `requirements.txt`): fastapi, uvicorn[standard], pydantic>=2, httpx, openpyxl, pytest, python-dotenv. `python3 -m venv backend/.venv && backend/.venv/bin/pip install -e backend -e core` (create `core/pyproject.toml` stub if B has not pushed yet; coordinate: B owns it, you may create the minimal stub and B replaces). `backend/payrollpilot/{__init__,app,db,contracts,permissions,events}.py`. `db.py`: SQLite document table + events + approvals + inbound_dedupe + send_log as in ARCHITECTURE section 4. `contracts.py`: pydantic models mirroring CONTRACTS sections 1-3 (keep field names identical). `permissions.py`: `check_recipient`, `check_send`, `check_apply`, `assert_not_gated`. `GET /api/health` reports adapter modes. `scripts/dev.sh` starts backend (and later bridge + web).
- Output: `uvicorn payrollpilot.app:app --port 8000` serves `/api/health` -> `{ok: true, contract_version: "1", integrations: {...: "unverified"}}`.
- Acceptance (FR-25, FR-26): restart the process; previously stored records and events still load. `check_recipient("+10000000000")` raises when not allowlisted. `assert_not_gated("source_write")` raises `NotImplementedError`.
- Verify: `cd backend && .venv/bin/pytest -q tests/test_a01_persistence.py tests/test_a01_permissions.py` -> expected `passed`.
- Fallback: if pydantic model work is slow, store raw dict JSON and validate only at route boundaries. Stop/escalate: cannot install fastapi within 10 min -> tell lead; use Python stdlib `http.server`? No: escalate first.
- Handoff: lead merges to `main`; C and D build against `/api/health` and the contracts module.

### A-02 Cycle load + audit + exceptions + events routes (P0) — 30 min
- Deps: A-01; B-01 fixture (use `docs/contracts/fixtures/cycle_synthetic_v1.json` as soon as B pushes; before that, build routes against your own 3-record mini fixture).
- Routes: `POST /api/cycles/load`, `GET /api/cycles/{id}`, `POST /api/cycles/{id}/audit` (import `payrollpilot_core.audit.run_audit`; if B's module is not merged yet, call a stub that returns `[]` and label `audit: "stub"` in health), `GET /api/cycles/{id}/exceptions` with filters, `GET /api/exceptions/{id}`, `GET /api/events`, `POST /api/approvals`, `POST /api/run/stop`.
- Acceptance (FR-01, FR-02, FR-08, FR-24): loaded cycle shows coverage rows, stage states `not_started`, destination `not_prepared`; audit on the synthetic fixture yields the exceptions in `expected_exceptions_v1.json` (category + entity refs); every exception has evidence and `provenance`; events list shows `cycle.created`, `audit.completed`, `exception.detected`.
- Verify: `backend/.venv/bin/pytest -q backend/tests/test_a02_routes.py`; `curl -s localhost:8000/api/cycles/cyc_synth_v1/exceptions | jq length`.
- Fallback: filters can be client-side if time is short (tell D).
- Handoff: D (board/inbox), F (contract tests), C (handoff route builds on exception state machine in `coordinator.py` which you create here with the transition table from CONTRACTS section 2; C extends it).

### A-03 Browser Use read of one real Jobber period (P0, timeboxed, independent) — 45 min, start after A-01 if owner has supplied `BROWSER_USE_API_KEY` and confirmed cycle dates; otherwise start A-02 first and come back
- Deps: owner: API key, Jobber login in a Browser Use profile (human-in-the-loop login, see docs.browser-use.com/cloud/guides/authentication.md), exact cycle dates confirmed against Gusto (O01). Not a dependency for any other lane.
- Steps: `backend/payrollpilot/adapters/browser_use.py`: create run with JSON-schema structured output for `{time_entries[], jobs[], workers[]}` for the exact date range; record `SourceCoverage` (range, count, complete flag, pagination note); write `data/private/snapshots/jobber_<start>_<end>.json` with `provenance: real`, `method: browser_use`. Read-only: the task prompt forbids edits and the run must not be given write-capable instructions; verify the profile is used only by this one run.
- Acceptance (FR-02, FR-07, T13): snapshot has `captured_at`, IDs/links, counts; partial reads labeled `complete: false` with reason; a second run with the same range dedupes by source IDs (no duplicate records after reload).
- Verify: `backend/.venv/bin/python -m payrollpilot.adapters.browser_use --start YYYY-MM-DD --end YYYY-MM-DD --dry-run` then real run; evidence: the run id and the snapshot's coverage block (no private data in the PR).
- Fallback: owner export (CSV/xlsx) -> `scripts/import_export.py` -> same snapshot shape, `method: owner_export`. If neither by 1:50 PM, the demo uses the synthetic fixture, labeled.
- Stop: 45 minutes or any sign of a write action -> stop and report.
- Handoff: load via `POST /api/cycles/load {source: "private_snapshot"}`; E notes "real read" vs "fixture" in the evidence matrix.

### A-04 Corrections apply + readiness + packet + workbook routes (P0) — 25 min
- Deps: A-02, B-02 (calc), B-03 (readiness), B-04 (workbook). Before deps land: write route shells returning `501 {"reason": "core not merged"}`.
- Routes: `POST /api/corrections`, `POST /api/corrections/{id}/apply` (requires `check_apply`; reruns audit + readiness; emits `correction.applied`, `recalc.completed`, `readiness.changed`), `GET /api/cycles/{id}/readiness`, `GET /api/cycles/{id}/packet`, `POST /api/cycles/{id}/workbook` (writes to `data/private/workbooks/` or `backend/data/`; returns `WorkbookArtifact` with `original_updated: false`).
- Acceptance (FR-13, FR-14, FR-16, FR-22, FR-28, T02, T16, T28): applying the T02 allocation correction leaves `stage1_wages_delta_cents == 0` and changes job costing; changing a source record after approval marks the approval `invalidated` (write a test that mutates the time entry version and asserts `approval.invalidated` event); workbook route reopens and verifies totals.
- Verify: `backend/.venv/bin/pytest -q backend/tests/test_a04_apply.py`.
- Handoff: D wires approval + readiness cards; E captures the "wages unchanged, job cost changed" screen.

### A-05 Gusto/QuickBooks owner-export importers (P1) — 20 min, only after A-04
- Owner-supplied rate/run-status export -> `Worker.rates` with `status: verified` and evidence `owner_export`; otherwise rates stay `unconfirmed` (blocker). No live Gusto/QBO API work today.

## Status log
(append status blocks here, format in shared context section 7)

```
LANE A status @ 12:40
Done: A-01 (acceptance checks passed: records+events reload after restart, both in pytest and a live uvicorn stop/start; check_recipient("+10000000000") raises PermissionDenied; assert_not_gated("source_write") raises NotImplementedError; /api/health returns ok, contract_version "1", integrations all unverified/blocked)
Changed files: backend/pyproject.toml, backend/.gitignore, backend/payrollpilot/{__init__,app,settings,state,db,events,contracts,permissions,coordinator,core_bridge}.py, backend/payrollpilot/routes/{__init__,health}.py, backend/payrollpilot/adapters/{__init__,messaging,memory,band}.py, backend/tests/{conftest,test_a01_persistence,test_a01_permissions}.py, scripts/{dev,smoke}.sh
Tests run: cd backend && .venv/bin/pytest -q tests/test_a01_persistence.py tests/test_a01_permissions.py -> 16 passed, 0 failed (1 starlette deprecation warning)
Evidence: live uvicorn :8000 health JSON; worker + cycle.created event reread after process restart
Blockers: none. Band setup check: all OK (CLI v0.4.16, Claude Code integration v0.5.33, session reachable).
Next: A-02
Handoff requested: C, D build against /api/health and backend/payrollpilot/contracts.py. contracts.py is lead-owned after this PR.
```

```
LANE A status @ 12:45
Done: A-02 routes (acceptance checks passed with lane A mini fixture: load shows coverage rows, stage states not_started, destination not_prepared; same-snapshot reload dedupes; exceptions carry evidence + provenance, unknown dollars stay null; events show cycle.created, snapshot.captured, audit.completed, exception.detected; approvals bind to current target version and supersede older ones; source_write/payroll_draft approvals return 501 gated; run/stop blocks audit and keeps approvals; state survives restart). Lane B's real cycle_synthetic_v1.json (from origin/lane/b-core, temp dir, not committed) loads: 7 coverage rows, not_started, not_prepared.
NOT done: "audit on the synthetic fixture yields expected_exceptions_v1.json" — blocked on B-02 (payrollpilot_core.audit not pushed). Test test_audit_matches_expected_exceptions is written and skips until fixture + core are present; /api/health shows audit: "stub" meanwhile.
Changed files: backend/payrollpilot/{kinds,cycles,approvals}.py, backend/payrollpilot/routes/{cycles,ops}.py, backend/payrollpilot/{app,routes/health}.py, backend/tests/test_a02_routes.py, backend/tests/fixtures/cycle_mini_v1.json
Tests run: cd backend && .venv/bin/pytest -q tests/ -> 27 passed, 2 skipped (lane B fixture/core not on branch), 0 failed
Evidence: live uvicorn :8000 + scripts/smoke.sh on cycle_synthetic_v1 and cycle_mini_v1 -> 200s, events [cycle.created, snapshot.captured, audit.completed]; audit after /api/run/stop -> 409 run_stopped
Blockers: B-02 for the expected-exceptions check. A-03: no backend/.env, so no BROWSER_USE_API_KEY and no confirmed cycle dates.
Next: A-04 route shells (501 until B-03/B-04), then A-03 when the owner supplies the key and dates.
Handoff requested: B: push core/payrollpilot_core/audit.py (run_audit(snapshot) -> list[dict]) and fixtures to main; then `backend/.venv/bin/pip install -e core` makes health show audit: "core". C: record kinds in backend/payrollpilot/kinds.py (message_batch, inbound, resolution); coordinator.transition_exception owns state changes. D: routes per CONTRACTS section 5; filters stage=stage1|stage2, category, state are server-side.
Correction: the A-01 block above originally said 12:58; the actual time was about 12:40.
```
