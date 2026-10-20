# Lane F: QA and integration

Owner: Codex session "F" (or a Claude Code session). Branch `lane/f-qa`, worktree `../PayrollPilot-f`. Binding: shared context, CONTRACTS, AGENTS.
Owns: `tests/integration/`, `core/tests/test_f_*.py`, `backend/tests/test_f_*.py`, `scripts/f_*.sh`. Reviews every lane's PR (comments only; never edits their files). Must not edit: anything outside owned paths.
Mission: contract tests that catch schema drift, regression tests for the no-duplicate / no-unauthorized / no-false-ready rules, failure/retry/privacy tests, and the integrated happy-path rehearsal at G1 and G2 with real results published.

## Tasks

### F-01 Contract and fixture tests (P0) — 25 min — start now
- Deps: B-01 fixtures (if not yet on main, write the tests against CONTRACTS.md shapes and mark pending).
- `tests/integration/test_contracts.py`: every fixture file loads; every record has `provenance`; money fields end in `_cents` and are int or null; durations `_minutes` int; exception states are in the allowed set; event types in the allowed list; no key named like a phone number or containing `@`; no fixture string matches real-name patterns the lead provides privately (keep a denylist in `data/private/denylist.txt`, test skips if missing).
- Verify: `python3 -m venv .venv-f && .venv-f/bin/pip install pytest && .venv-f/bin/pytest -q tests/integration/test_contracts.py`.

### F-02 Safety regression suite (P0) — 30 min
- Deps: A-01 (permissions), B-03 (readiness), C-05 (routes) as they land; write tests early, mark `xfail(strict=False)` with the task id until the code merges, then flip.
- Tests (map to PRD): no duplicate send on retry (T14, T16: call send twice -> second returns `already_sent`); inbound replay processed once (T14); non-allowlisted recipient refused in backend and bridge (FR-10, FR-26); approval version mismatch refuses apply (FR-23); source change invalidates approval (T16); T17 injection -> `blocked.unauthorized_instruction`, no state change; readiness never `ready` with a null required input (T11, T22); manager-pool blocker does not alter commission readiness (T24); allocation correction leaves wages unchanged (T02); workbook totals equal packet (T28); restart preserves cases and approvals (T18, FR-25); gated actions raise (`source_write`, `payroll_submit`).
- Verify: `backend/.venv/bin/pytest -q backend/tests/test_f_safety.py core/tests/test_f_rules.py` with results pasted.

### F-03 Integrated rehearsal at G1 and G2 (P0) — 20 min each
- `scripts/f_smoke.sh`: start backend + bridge + web (or use `scripts/dev.sh`), load fixture, audit, draft, approve, send (real, to the allowlisted handle; owner replies per `demo/reply-script.md`), inbound, parse, correction, apply, readiness, packet, workbook, memory recall-check; print each step's HTTP status and key ids. Run at G1 (1:50 PM) and G2 (2:20 PM); publish the transcript in `tests/integration/REHEARSAL.md` with pass/fail per step and the exact failures. Review each lane's open PR for ownership violations, secrets, and unlabeled fakes; comment.
- Acceptance (FR-25, FR-29, FR-30): rehearsal transcript exists with real statuses; blockers routed to the owning lane and the lead.

### F-04 Privacy sweep before recording (P0) — 10 min at 2:35 PM
- `scripts/f_privacy.sh`: grep the repo and `web/dist` for E.164 numbers, `sk-or-`, `@gmail`, the private denylist terms; check `.gitignore` covers `docs/private`, `data/private`, `.env`; confirm `git ls-files` includes no xlsx outside fixtures. Report results.

## Status log

```
LANE F status @ 13:03
Done: F-01 (acceptance checks passed: all 5 fixtures load; money *_cents int or null, durations *_minutes int or null, no float money; snapshot records validate against backend pydantic models (cycle, workers, time entries, jobs, receipts, costs, obligations); core run_audit output and cycle_readiness items validate against PayrollException / Readiness / CompensationItem; exception state and category enums equal between CONTRACTS.md and contracts.py; event types and actors equal between CONTRACTS.md section 4 and events.py; replies fixture covers clean / T14 / conflicting / T17 and placeholders resolve; no phone, email or E.164 values (fictional 555 number allowed); display names de-identified; manager split is placeholder and differs from the private allocation)
Changed files: tests/integration/test_contracts.py
Tests run: backend/.venv/bin/pytest -q tests/integration/test_contracts.py -> 32 passed, 5 skipped (denylist absent), 1 xfailed
Evidence: xfail = CONTRACTS Receipt has no provenance field while AGENTS.md says every record carries provenance
Blockers: data/private/denylist.txt not supplied, so the denylist test skips. Lead decision: add provenance to Receipt (contract + fixture) or exempt it.
Next: F-02 safety regression suite
Handoff requested: lead supplies data/private/denylist.txt (one term per line, gitignored)
```
