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

```
LANE A status @ 12:47
Done: A-04 lane A parts (acceptance checks passed: apply refused without approval (403) and with a stale version (409); approved job_allocation applies as a local overlay, source snapshot unchanged, audit re-run on corrected view drops the missing_job case, events correction.proposed/approval.granted/correction.applied/recalc.completed; T16: changing the time entry version_hash in the source after approval invalidates the approval and the correction (approval.invalidated event) and apply returns 403; a correction applies once). Lane C hooks: guarded routes_comms include + coordinator.transition (in #9).
NOT done: T02 numbers (wages delta 0, job cost delta) and readiness/packet/workbook outputs — need lane B's propose_correction, readiness, packet, workbook. Those routes return 501 {"reason": "core not merged"}; tested.
Changed files: backend/payrollpilot/{corrections,core_bridge,cycles,permissions,contracts,app}.py, routes/{payroll,health}.py, backend/tests/test_a04_apply.py
Tests run: cd backend && .venv/bin/pytest -q tests/ -> 34 passed, 1 skipped (expected-exceptions: needs payrollpilot_core.audit), 0 failed. Lane B fixture load test ran against a local uncommitted copy of origin/lane/b-core fixtures and passed.
Evidence: tests above; /api/health now shows core: {audit, corrections, readiness, packet, workbook} modes
Blockers: lane B core modules; A-03 still needs BROWSER_USE_API_KEY + cycle dates in backend/.env
Next: wire real core signatures when B pushes; A-03 when unblocked; A-05 after
Handoff requested: C/D: message approval target_version = batch text_hash = permissions.text_hash(text) (CONTRACTS); correction approval target_version = the `target_version` field returned by POST /api/corrections and GET /api/corrections/{id}.
```

```
LANE A status @ 12:58
Done: readiness route rewired to lane B's cycle_readiness(view, exceptions, policies) per B's request; private policy overrides read from data/private/policy.json (PP_POLICY_FILE) when present, else None. Integration check with lane B PR #11 core installed temporarily into backend/.venv (from origin/lane/b-03): A-02 expected-exceptions acceptance now PASSES (15 of 15 by category + entity refs, all with evidence + provenance).
Tests run: with lane B core: cd backend && .venv/bin/pytest -q tests/ -> 36 passed, 0 skipped, 0 failed. Without core (uninstalled after): 34 passed, 2 skipped, 0 failed.
Evidence: live uvicorn + scripts/smoke.sh cycle_synthetic_v1 with core -> 15 exceptions, 15 exception.detected events; GET /readiness -> stage1 partial "review-ready for 1 of 4 workers; 3 unresolved; 1 out-of-cycle entry excluded"; quote job_01 pending (exception blockers), quote job_02 not_meaningful, marketing pending policy_missing:O04, tip pending policy_missing:O07 + prior_payment_unknown, manager_pool blocked policy_missing:O05/O06 + coverage:expenses.
Blockers: B-04/B-05 (packet, workbook, propose_correction) for the rest of A-04; A-03 needs backend/.env key + dates.
Next: wire propose_correction/packet/workbook when B pushes; then A-03/A-05.
```

```
LANE A status @ 13:02
Done: A-04 complete against lane B core (acceptance checks passed: T02 end to end through routes on cycle_synthetic_v1 with real core from main — te_0014 job_01 -> job_02 gives stage1_wages_delta_cents 0, job_01/job_02 labor deltas equal and opposite, approval -> apply -> stage1 readiness unchanged and equal to readiness_matrix_v1 after_t02_correction; T16 approval invalidation; packet + workbook routes with lane B PR #15 installed temporarily: 12 ledgers + Sources, verified_totals, original_updated false, workbook.generated + workbook.verified events; WorkbookVerificationError -> 500, no success events; lane B CorrectionError codes map to HTTP: stale_before/allocation_mismatch 409, target_not_found 404, others incl. unsupported:* 422)
Changed files: backend/payrollpilot/corrections.py, backend/payrollpilot/routes/payroll.py, backend/tests/test_a04_apply.py, docs/plans/A-platform-data.md
Tests run: cd backend && .venv/bin/pytest -q tests/ -> with main core: 56 passed, 1 skipped (packet/workbook: B-04 not on main), 0 failed; with lane B PR #15 core installed temporarily: 57 passed, 0 failed
Evidence: live workbook wb_40f0f25c89 draft_c8074d1db110 (private, data/private/workbooks): sheets Review..Carry-forward + Sources; verified_totals stage1_gross_ready_cents 174900, stage1_gross_all_cents null, cycle_profit_cents null (unknown stays null)
Blockers: none for A-04 once lane B PR #15 merges. A-03 still needs BROWSER_USE_API_KEY + cycle dates in backend/.env.
Next: A-03 when unblocked; else A-05 owner-export importers
Handoff requested: lead merges this, then lane B PR #15; after both, packet/workbook test runs unskipped. D: POST /api/corrections returns target_version + blockers; workbook path is private, do not render it.
```

```
LANE A status @ 13:10
Done: A-04 fix for lane F's G1 blocker (acceptance checks passed: after the approved T02 correction is applied, the already_paid_allocation exception on te_0014 is resolved (new version + exception.state_changed with correction_id/approval_id) before readiness is recomputed; ci_quote_job_01 loses exactly that blocker; no other case is resolved; Stage 1 unchanged)
Scope: only exceptions that (a) reference a record the applied correction touched and (b) the corrected-view audit no longer detects are resolved (coordinator.resolve_by_applied_correction). Not every non-redetected exception: that would close cases that vanished for other reasons. Reopen rule added per CONTRACTS: resolved -> detected only when the detection content changes (source change); a case resolved by reply but still detected unchanged stays resolved.
Changed files: backend/payrollpilot/{coordinator,corrections,cycles}.py, backend/payrollpilot/routes/payroll.py (REPO_ROOT name kept importable: lane F's fixture monkeypatches it), backend/tests/test_a04_apply.py
Tests run: cd backend && .venv/bin/pytest -q tests/ -> 69 passed, 0 failed. Lane F's tests/test_f_safety.py (from ../PayrollPilot-f, not committed here) as-is: 15 passed, 5 skipped, 1 failed = the strict xfail now passing (expected signal); with the xfail marker removed: 16 passed, 5 skipped.
Blockers: none. A-03 still needs BROWSER_USE_API_KEY + cycle dates in backend/.env.
Next: A-03 when unblocked, else A-05
Handoff requested: F removes the xfail marker on test_t02_apply_clears_the_fixed_exception_from_readiness after this merges.
```

```
LANE A status @ 13:14
Done: A-03 prep (acceptance so far: key verified with one GET /profiles -> 200; profile payrollpilot-jobber-readonly created; plain login browser session opened on it (no agent), live link in data/private/browser_use/login_link.txt (gitignored, 0600), session timeout 13:42 PT; read command built: read-only task prompt, JSON-schema structured output, de-identified snapshot -> data/private/snapshots/jobber_<start>_<end>.json, coverage complete only when all pages viewed and counts match, unknown durations null, second read dedupes by Jobber id, private snapshot loads + audits through the routes)
NOT done: the real read. Waiting on (1) owner Jobber login in the live browser, (2) owner-confirmed pay-period dates. Timebox 45 min starts when dates arrive.
Changed files: backend/payrollpilot/adapters/browser_use.py, backend/tests/test_a03_browser_use.py, docs/plans/A-platform-data.md
Tests run: cd backend && .venv/bin/pytest -q tests/ -> 74 passed, 0 failed (A-03: 5 passed, no network)
Evidence: profile c3993dee-fbab-4ab8-b294-04179dcbdf29, login session 3b7b9253-7bd4-45a1-9c79-e30399926ffd; dry run prints task + schema, no API call
Blockers: owner login + dates
Next: on "logged in": stop session (saves cookies), confirm jobber cookie domain; on dates: read, load via POST /api/cycles/load {source: private_snapshot}
Handoff requested: lead relays the owner's "logged in" and the dates
```
