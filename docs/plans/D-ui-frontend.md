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

```
LANE D status @ 12:43
Done: D-01 (acceptance checks passed: placeholder fixture renders; blockers display with codes; null money renders as a dash; Stage 2 summary lists items separately and never says "complete"; 1280px and 375px layouts checked, no horizontal overflow at 375px)
Changed files: web/ (new: Vite + React 19 + TS strict, src/contracts.ts zod mirror of CONTRACTS v1.1, src/api.ts data layer with VITE_DATA_MODE=fixture|api, src/fixtures/placeholder_bundle.json, src/screens/Board.tsx, scripts/check-contracts.ts, screenshots/)
Tests run: cd web && npm install && npm run build -> exit 0; npm run check:contracts -> 15/15 checks passed
Evidence: web/screenshots/d01-board-1280.png, web/screenshots/d01-board-phone-375.jpg
Blockers: lane B fixtures not yet in docs/contracts/fixtures/ on main; board uses the lane D placeholder bundle (labeled synthetic). Band setup check: OK (CLI v0.4.16, Claude Code integration v0.5.33, session reachable).
Next: D-02 inbox + thread
Handoff requested: A: no GET route for workers/display names (board falls back to /packet identities, else worker_id); no API field for labor/revenue review or cash confirmation (UI shows "not reviewed" / "not confirmed"). E: screenshots above.
```
```
LANE D status @ 12:54
Done: D-02 (acceptance checks passed in fixture mode, driven in the browser: T14 vague "yes" to 3 grouped questions shows 3x ambiguous + Clarify; T17 injection reply shows "Blocked instruction" badge and the number in the reply is masked; approval dialog shows exact text, masked recipient, linked issue ids, version; editing text after "Approve only" invalidates the approval and requires re-approval; T02 flow draft, approve+send, conflicting reply, clarify, confirmed follow-up, resolution, propose, approve, apply changes board readiness: T02 blocker leaves the quote commission card, open exceptions 15 to 14)
Also: fixture mode now renders lane B fixtures (build-fixtures converter), shared film tokens adopted from lane E.
Changed files: web/src/screens/Inbox.tsx, Thread.tsx, components/ApprovalDialog.tsx, src/sim.ts, src/api.ts, src/format.ts, src/index.css, scripts/build-fixtures.mjs, scripts/check-contracts.ts, screenshots/d02-*
Tests run: cd web && npm run build -> exit 0; npm run check:contracts -> 19/19 checks passed. Not run: D-02 against the live API (A-02 not on main yet).
Evidence: web/screenshots/d02-approval-dialog.jpg, d02-thread-clarify-resolve.jpg, d02-inbox-t17-blocked.jpg, d02-inbox-t14-grouped-1280.jpg
Blockers: none for fixture mode. Live API untested.
Next: D-03 activity, review, workbook panel
Handoff requested: A/C: GET /api/exceptions/{id} "messages" shape is unpinned (UI accepts batches and inbound mixed, plus parsed/approvals arrays); LocalCorrection has no version hash for approval target_version (UI uses version_hash if present, else a client hash); no route to edit a draft; T17 blocked flag is read from blocked.unauthorized_instruction events whose refs name the inbound id. Lead: PRODUCT-STATEMENT lists a "playback" provenance that CONTRACTS does not have.
```
```
LANE D status @ 13:04
Done: D-03, rebuilt as the owner's one-screen decision (docs/UI-ONE-SCREEN.md) in the light register (docs/DESIGN-DIRECTION.md, lane G tokens). Acceptance checks passed in fixture mode, driven in the browser: zone 1 pipeline Collect/Audit/Resolve/Prepare/Review shows each agent's last event; Stage 1 and Stage 2 rows never merge and never say "complete"; Stage 2 chips list each item state with blocker counts; activity log is collapsible with actor filter and highlights handoff, memory.applied and blocked events; zone 2 groups blockers by respondent (Ops lead, Workers, Owner, Resolved) with "Draft one message"; owner rows are decisions, not texts; zone 3 is the D-02 thread. T02 flow end to end on one screen: quote commission 8 to 7 blockers, open 15 to 14, every pipeline step lit. Workbook toast states "Original workbook not updated" and shows draft version, sheets and verified totals; Stop run posts /api/run/stop. Phone width 375px: no horizontal overflow.
Changed files: web/src/screens/CommandCenter.tsx (new), Board.tsx and Inbox.tsx removed (folded in), Thread.tsx, App.tsx, api.ts, sim.ts, components/ui.tsx, index.css, screenshots/d03-*
Tests run: cd web && npm run build -> exit 0; npm run check:contracts -> 19/19 checks passed. Not run: live API mode (no backend on :8000 in this session). Workbook export only renders an error toast in fixture mode by design.
Evidence: web/screenshots/d03-command-center-1280.jpg, d03-zones-thread-1280.jpg, d03-after-correction-1280.jpg, d03-command-center-phone-375.jpg
Blockers: none for fixture mode. Live API smoke test still owed.
Next: D-04 polish; live API smoke test once a backend is running
Handoff requested: A: packet route returns 501 until build_packet lands, so per-worker minutes show a dash; data layer already reads A-02 exception detail (messages.outbound/inbound) and A-04 correction target_version. A/C: no route for an owner decision (policy_missing, rate confirmation), so owner rows show the decision text only. E: light-register screenshots above.
```

```
LANE D status @ 13:43
Done: D-04 follow-up on lane/d-web-04 after #33 merged. Frozen home/ready tokens retained at /; Details retained. API readiness supplies worker counts; detected-case drafts are discovered; server-issued correction target_version is fetched before approval; message approval posts exact text_hash before send; actions remain disabled until refreshed state arrives. Six progress segments honor stage states, including the ready state; activity is ordered plain English with evidence-based test labels. Exact payroll dates survive phone masking. Fake messaging is labeled.
Owner-approved scope exception: narrow backend POST /api/messages/{id}/edit and /decline routes added in routes_comms.py, plus a two-line declined-target refusal in approvals.py. Edit checks current text_hash, appends a draft version, invalidates approvals. Decline persists declined_at, invalidates approvals and refuses subsequent approval/send. A dedicated process lock serializes send/edit/decline. No changes to permissions.py, financial rules, shared contracts, source writes or payroll submission.
Changed files: web/src/{screens/Home.tsx,screens/Thread.tsx,home-state.ts,home.css,api.ts,contracts.ts,format.ts,sim.ts}; web/scripts/check-home-{state.ts,browser.mjs}; web/screenshots/d04-home-api-1280.png; backend/payrollpilot/{routes_comms.py,approvals.py}; backend/tests/test_d04_draft_actions.py; own Status log only.
Tests run: VITE_DATA_MODE=api npm run build -> exit 0; npm run check:contracts -> 22/22; node --import tsx scripts/check-home-state.ts -> exit 0; PYTHONPATH=backend:core <existing Python venv>/bin/python -m pytest backend/tests core/tests -q -> 257 passed. Browser QA against separate fake-messaging API :18000 and web :5174 passed exact preview, masked recipient, Edit, Approve/Send order+hash, Approve/Apply version, persistent Decline after reload, Pause/Resume, event-error recovery, no 375px overflow, six-step ready presentation, and Details navigation. Ready presentation uses explicit API-shaped stage overrides and is not real readiness evidence.
Evidence: web/screenshots/d04-home-api-1280.png (actual API data, isolated synthetic cycle, FakeMessaging). Live backend :8000 and bridge :3001 were not changed or restarted; no real sends from QA.
Blockers: none for requested message/correction actions. Payroll-draft approval remains gated by the existing backend and is shown unavailable; no invented commission/tip aggregate or fake workbook download.
Next: lead review and merge of the one D-04 follow-up PR; coordinate live backend refresh with C without restarting its services.
Handoff requested: lead review the owner-approved backend ownership exception; C owns adoption of the new edit/decline routes in its running process.
```

```
LANE D status @ 14:00
Done: D-05 between-payrolls home from the owner's supplied HTML ZIP. Native React/CSS matches all four reference card bounds exactly at 1280px; pixel comparison differs by 0.006% (>20/channel threshold), excluding the separate explicit preview banner. Phone 375px has no horizontal overflow. /preview/between-payrolls is labeled synthetic/design-only. / can select idle only from a valid explicit idle_home payload after successful load, with no paused run, unresolved exception, pending message or pending correction. Existing approval actions take precedence, including drafts attached to resolved cases. Historical approval/submission badges require existing verified cycle state. Unknown money remains a dash; unsupported scheduling/download controls are disabled.
Lead coordination: lead confirmed no backend idle/schedule data source exists and approved a web-only explicit-payload seam plus labeled preview. No backend or shared-contract change. Live UI blocker addressed separately: original PayrollPilot-d/web was clean at f0b7847; adopted only the already-merged api.thread correction-version GET patch there via HMR. Existing :5173 Approve & Apply was verified visible/enabled with zero non-GET requests. C/lead notified; no owner approval clicked and no backend/bridge restart by D.
Changed files: web/src/{App.tsx,screens/Home.tsx,screens/BetweenPayrolls.tsx,idle-state.ts,idle.css,fixtures/idle-preview.ts}; web/scripts/check-idle-{state.ts,browser.mjs}; web/IDLE-HOME.md; web/screenshots/d05-idle-preview-{1280,phone}.png; own Status log.
Tests run: VITE_DATA_MODE=api npm run build -> exit 0; npm run check:contracts -> 22/22; node --import tsx scripts/check-home-state.ts -> pass; node --import tsx scripts/check-idle-state.ts -> pass; check-idle-browser.mjs -> pass (ZIP comparison, 375px layout, read-only controls, explicit API activation, missing/error fallbacks, message/correction precedence and Details). Existing check-home-browser.mjs -> pass against a separate FakeMessaging API :18000, including exact-version Approve/Send, Approve/Apply, Edit, persisted Decline, Pause/Resume and recovery. No live messages sent by QA.
Evidence: web/screenshots/d05-idle-preview-1280.png and d05-idle-preview-phone.png; schema/source limitations and test commands in web/IDLE-HOME.md.
Blockers: current backend does not emit idle_home or operate a payroll scheduler; production / therefore keeps its approval view. Preview controls cannot change schedules or download a nonexistent workbook.
Next: lead review/merge the focused D-05 PR. Backend lifecycle/scheduler work remains outside this web-only scope.
```
