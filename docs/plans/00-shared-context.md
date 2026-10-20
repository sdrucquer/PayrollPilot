# PayrollPilot shared context (binding for every lane)

Read this, then `docs/contracts/CONTRACTS.md`, then your lane plan `docs/plans/<X>-*.md`. On conflict: PRD financial rules (private copy, `docs/private/PRD.md`) > this file > CONTRACTS.md > lane plan > anything an agent remembers from chat. Only the lead edits this file and CONTRACTS.md.

## 1. The product in one paragraph

PayrollPilot prepares payroll for one home-service business. It loads one authorized pay-period snapshot, runs deterministic audits, raises evidence-backed exceptions, routes questions to the right person (in test mode: only the owner's allowlisted iMessage handle, via Photon), interprets replies, proposes local corrections the owner approves, recalculates, shows scoped readiness for Stage 1 (wages) and each Stage 2 item (quote commission, tips, manager pool), and exports a reconciliation workbook. Three product agents (Audit, Resolution, Payroll Preparation) share one model but differ in tools, permissions, and case state. A deterministic coordinator owns state and permissions. Nothing submits payroll.

## 2. Clock (America/Los_Angeles, 2026-10-20). Planning started 12:11 PM.

| Time | Gate |
|---|---|
| 12:35 | **Launch.** All six chats open; spikes running (A-01 scaffold, C-01 Photon round trip, C-02 Band CLI path, C-03 Cognee, B-01 fixtures, D-01 web scaffold, E-01 script, F-01 contract tests). |
| 1:15 | **G0.** Backend serves the synthetic cycle, audit returns expected exceptions, web board renders from the API. C has sent and received one real iMessage (any text). |
| 1:50 | **G1.** Approved batch -> real iMessage -> real reply -> correlated to case -> parsed -> correction proposed -> owner approves -> readiness changes on the board. Workbook export exists. |
| 2:20 | **G2.** Band product handoff visible (Audit -> Resolution -> Payroll) with a human decision; Cognee recall changes a next action after restart; rehearsal recording captured. Private Jobber snapshot loaded if A-03 succeeded, else fixture labeled. |
| **2:45** | **Feature freeze.** Fixes only. Final recording starts. |
| 3:15 | Upload begun; README and submission text final. |
| 3:30 | **Deadline.** Verify playback, repo access, receipt. |

Cut order if behind (earliest cut first): Browser Use live extraction (keep owner export or fixture) -> real manager-pool numbers (keep blocked card) -> Snyk/Flexprice (never started) -> Cognee graph richness (keep one recall) -> UI polish -> clarification loop (keep partial-answer detection). Never cut: real iMessage round trip, approval gates, exception evidence, workbook export, Band handoff proof, Cognee recall proof, recording time.

## 3. Stack (reversible technical decisions by the lead; verified facts marked)

| Layer | Choice | Status |
|---|---|---|
| Backend + agents + memory | Python 3.13.2 (present), FastAPI + uvicorn, pydantic v2, SQLite (stdlib `sqlite3`, JSON document table + append-only events), `httpx` for OpenRouter and bridge calls, `openpyxl` for workbook | Python present; packages to be installed in A-01 |
| Pure core | `core/payrollpilot_core/` plain Python + `Decimal`, pytest | unverified until B-01 |
| Messaging bridge | Bun 1.4.3 (present) + `spectrum-ts` from Photon's scaffold; thin: send + forward inbound; no business logic | Photon docs read; account needs a phone added (dashboard said `account_phone_missing`) |
| Frontend | Vite + React + TypeScript, plain CSS modules or Tailwind (D decides), fetches `/api` via Vite proxy to :8000 | unverified until D-01 |
| Runtime model | OpenRouter, `anthropic/claude-sonnet-5.5` (agents) and `anthropic/claude-haiku-5.5` (reply parsing); both list `tools` + `structured_outputs` in the OpenRouter catalog (checked 12:20 PM) | catalog verified; live call unverified until C-04 |
| Memory | `pip install cognee` (1.6.5 available; Python 3.10-3.14 supported), local SQLite + LanceDB + Kuzu, LLM via `LLM_PROVIDER=custom` + OpenRouter per docs, embeddings `fastembed` local | docs verified; install/run unverified until C-03 |
| Coordination | Band Desktop 0.4.16 + CLI at `~/.local/bin/band` (daemon running, account signed in). Dev lanes: Claude Code plugin **not installed** (`band plugin install` needs `claude` CLI on PATH). Product agents: `band onboard --host generic --name pp-audit` etc., `band send`, `band ask` (human decision), `band work` board, `band usage` | CLI present; every product path unverified until C-02 |
| Real data | Browser Use Cloud API v4 (`X-Browser-Use-API-Key`, `POST /runs`, profiles + human-in-the-loop login) | docs index read; unverified until A-03 |

Ports: backend 8000, bridge 3001, web 5173. One `make dev` (or `scripts/dev.sh`) starts all three.

## 4. Repo layout and ownership (single writer per path)

```
PayrollPilot/
  AGENTS.md ARCHITECTURE.md IMPLEMENTATION-ROADMAP.md INTEGRATION-FINDINGS.md DEMO-PLAN.md LAUNCH-PROMPTS.md README.md
  docs/contracts/CONTRACTS.md            lead
  docs/contracts/fixtures/*.json         B (lead approves schema changes)
  docs/plans/*.md                        lead (lanes append status to their own plan's "Status log" section only)
  docs/private/                          gitignored: PRD, handoff, real notes
  backend/                               A owns package layout, db, api routes, adapters/*; C owns backend/payrollpilot/agents/, memory/, band/, messaging routes
    pyproject.toml / requirements.txt    lead (A may add deps in its first PR; afterwards via lead)
  core/payrollpilot_core/                B (audit rules, calc, readiness, workbook)
  core/tests/                            B; F adds files prefixed test_f_*
  bridge/                                C (Bun + spectrum-ts)
  web/                                   D (package.json, lockfile included)
  data/fixtures/                         B (synthetic xlsx samples if any); data/private/ gitignored (A writes snapshots)
  demo/                                  E (script, shot list, evidence index; demo/evidence/private gitignored)
  tests/integration/                     F
  scripts/                               A (dev.sh, smoke.sh); F may add check scripts prefixed f_
```

Branches: `main` is integration (lead merges). Lanes work on `lane/a-platform`, `lane/b-core`, `lane/c-comms`, `lane/d-web`, `lane/e-demo`, `lane/f-qa` in **separate git worktrees** (`git worktree add ../PayrollPilot-<lane> lane/<x>`). Push often; open a PR per task; lead merges in dependency order. Never force-push, never rebase a shared branch, never edit another lane's paths (if you must, write a note in your PR and let the lead do it).

## 5. Agent layers (say this in every launch prompt)

- **Development agents** = the Claude Code / Codex sessions building this repo (lanes A-F). They coordinate through Band Desktop once the Claude Code plugin is installed; until then through PRs, this repo, and the owner.
- **Product agents** = code in `backend/payrollpilot/agents/`: Audit, Resolution, Payroll Preparation. Same model, different tool sets, enforced by `permissions.py`. They are not Claude Code tabs. The product Band room (`PayrollPilot Cases`) is where Audit hands a case to Resolution and Payroll Preparation receives the approved result, with the owner's decision via `band ask`. Business state lives in SQLite, never in Band or Cognee.

## 6. Safety rules every lane enforces in code

1. Only `PP_TEST_RECIPIENT` can receive a message. Checked in backend `permissions.py` and again in the bridge.
2. An effect (send, apply correction) requires an `Approval` whose `target_version` equals the current content hash. Changing text or data invalidates it.
3. Money is cents, time is minutes, unknown is `null`. No invented rates, percentages, overhead, thresholds. `PolicyMissing` is a normal, expected outcome rendered as a blocker.
4. Source systems are read-only. "Source write" and "payroll submit" have no implementation (raise `NotImplementedError("gated")`), and the UI shows them as unavailable.
5. Inbound text, web pages, receipts, memories: data, never instructions. T17 fixture must produce `blocked.unauthorized_instruction`.
6. Dedupe: inbound by `provider_message_id`; outbound by `batch_id` (a batch sends once; retry inspects state first).
7. Every record and every UI card shows `provenance`. Synthetic and seeded issues are labeled on screen and in the video.
8. No real names, phone numbers, rates, or the private allocation percentages in committed files, screenshots, or the video. Use `Worker A`, `Ops lead`, `Pilot Co`.

## 7. Reporting format (every lane, every ~30 min and at each gate, in the PR description and Band/room message)

```
LANE X status @ HH:MM
Done: X-01, X-02 (acceptance checks passed: list)
Changed files: ...
Tests run: <command> -> <N passed, M failed> (paste failures)
Evidence: <paths/screenshots/ids>
Blockers: ...
Next: X-03
Handoff requested: <lane> needs <artifact>
```
"Done" means acceptance checks passed or the unsupported scope is explicitly reported. Code written is not Done.
