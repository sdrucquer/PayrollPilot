# Lane D: UI and frontend

Owner: Claude Code session "D". Branch `lane/d-web`, worktree `../PayrollPilot-d`. Binding: shared context, CONTRACTS, AGENTS.
Owns: `web/` entirely (including `web/package.json` and lockfile), `web/src/contracts.ts`. Must not edit: `backend/`, `core/`, `bridge/`, `demo/`, plans. Single owner of production UI; an optional design chat only supplies a spec you may adopt.
Mission: a working app (not a mockup) with four screens from PRD 7.2: cycle board, exception inbox + thread, agent activity, review/approval, plus workbook controls. Build against fixtures first, then the real `/api`. Every card shows `provenance` and `Readiness` honestly. The UI never computes money.

Stack: Vite + React 18 + TypeScript strict. Styling: Tailwind or CSS modules (your call, one of them, no component library beyond headless if needed). Vite dev proxy `/api` -> `http://127.0.0.1:8000`. Money formatter `formatCents(n|null)` renders `—` for null, never `$0`. Minutes formatter `134 -> 2h 14m`.

Fixture-first rule: `web/src/fixtures/` loads `docs/contracts/fixtures/*.json` (copy them in at build via a tiny script or import with `?raw`). `VITE_DATA_MODE=fixture|api` switches the data layer; `api` is default once A-02 is on main. The data layer (`web/src/api.ts`) is the only place that knows the difference.

## Tasks

### D-01 Scaffold + data layer + board (P0) — 30 min — start now
- Deps: none (fixtures from B land ~12:55; before that, hand-write a 3-item placeholder matching CONTRACTS and replace).
- Screens: `/` Cycle board: company label, period, timezone, existing-run status, coverage chips (per dataset: complete/incomplete, method), Stage 1 card (`StageState` + worker-level readiness list), Stage 2 cards: Quote/marketing, Tips, Manager pool, each rendering `Readiness` (state, scope, blockers with codes, unknown amount), plus three separate indicators: wage correctness, labor/revenue review, cash confirmation (`not confirmed` by default). Destination badge (`internal_draft` / `not_prepared`). Never show the word "complete" for a stage.
- Acceptance (FR-24, FR-27, T22, T24, T30): fixture renders; blockers display; null money shows `—`; a stage summary line lists items separately ("1 commission ready; tips pending; manager pool blocked").
- Verify: `cd web && npm install && npm run build && npm run check:contracts` (write this script: validates fixture JSON against `contracts.ts` zod/TS types, or at least a shape check) -> exit 0. Screenshot board at 1280px and phone width.
- Handoff: E gets the screenshot; A gets any field mismatch note.

### D-02 Exception inbox + thread (P0) — 30 min
- Deps: D-01; A-02 for live data.
- `/inbox`: list with filters (wages, costs, commissions, prior payment, policy; state), each row: title, category, stage impact, intended respondent role (label only), state, next action, provenance tag. `/inbox/:id` thread: observed vs expected, evidence refs (system + record id + link if any), stage impact, message batches (text, masked recipient, state, provider status), inbound replies (raw text, `test_reply` label, parsed answer status), resolution, correction, and action buttons wired to `/api`: Draft question (POST messages/draft), Approve + Send (creates approval with `target_version = text_hash`, then send), Clarify, Propose correction, Approve correction (approval kind local_correction), Apply.
- Acceptance (FR-08 to FR-13, T14, T17): a vague reply shows per-question `ambiguous` and a Clarify button; the T17 injection reply shows a "blocked instruction" badge; approval dialog shows exact text + masked recipient + linked issue ids before send; after text changes the approve button requires re-approval.
- Verify: `npm run build`; manual flow against FakeMessaging in dev; screenshots of the approval dialog.

### D-03 Agent activity + review/approval + workbook controls (P0) — 25 min
- Deps: D-01; A-02 events; A-04 packet/workbook.
- `/activity`: event feed (actor, type, summary, refs, duration, usage tokens/cost when present), filter by actor; `memory.applied` and `handoff.*` events visually distinct; show `provenance`/integration mode from `/api/health` in a header strip ("Messaging: live Photon | Memory: Cognee | Band: enabled").
- `/review`: packet view (period, identities as display names, earnings table per worker per workweek: minutes, rate status, gross or `—`, prior obligations, outstanding items), separate approval records list (kind, target, version, state), workbook panel: Generate button -> shows `WorkbookArtifact` (draft version, sheets present, verified totals, `original_updated: false` with the note), destination status "Gusto: not prepared".
- Acceptance (FR-16, FR-22, FR-24, FR-28, T28): workbook panel never claims the original was updated; packet draft version equals the workbook's.
- Verify: `npm run build`; screenshots.

### D-04 Polish for recording (P1) — after G1
- Loading/error states (integration errors show as errors, not success), stop control (POST /run/stop) visible, dark text contrast, no phone numbers anywhere (mask helper everywhere a recipient appears).

## Status log
