# Lane C: Communication, product agents, Band, Cognee

Owner: Claude Code session "C". Branch `lane/c-comms`, worktree `../PayrollPilot-c`. Binding: shared context, CONTRACTS, AGENTS, INTEGRATION-FINDINGS.
Owns: `bridge/` (Bun + spectrum-ts), `backend/payrollpilot/agents/`, `backend/payrollpilot/memory/`, `backend/payrollpilot/band/`, `backend/payrollpilot/adapters/messaging.py`, `backend/payrollpilot/routes_comms.py` (handoff, messages draft/send, inbound, clarify, memory recall-check). Must not edit: `backend/payrollpilot/{app,db,contracts,permissions,coordinator}.py` (lane A; request changes via PR note), `core/`, `web/`, `demo/`. Register your router in `app.py` through a one-line include that A adds (ask A in your first status).
Mission: a real approved iMessage reaches the owner's phone; a real reply enters the right case; the Band room shows Audit -> Resolution -> Payroll handoffs with a human decision; Cognee stores a scoped resolution that a restarted process recalls and acts on. Every proof is recorded in `INTEGRATION-FINDINGS.md` with status + evidence.

Human prerequisites (ask the owner in your first message, then proceed with spikes that do not need them):
1. Photon: add a phone to the account (avatar menu, top-right; dashboard currently says `account_phone_missing`). Then scaffold writes credentials to `bridge/.env`. Put the owner's iMessage handle in `PP_TEST_RECIPIENT` (bridge/.env and backend/.env). Never paste it in chat or files.
2. `OPENROUTER_API_KEY` in `backend/.env` (and `LLM_API_KEY` same value for Cognee).
3. Band Claude Code plugin: lead is installing the `claude` CLI and running `band plugin install`; your session may need a restart to pick it up.

## Tasks (C-01, C-02, C-03 are independent spikes; run C-01 first, then C-03 while waiting on the phone step, then C-02)

### C-01 Photon iMessage round trip (P0) — 30 min from phone added
- Steps: `cd bridge && bun create spectrum-project@latest . --projectId <id from dashboard> --providers imessage --yes` (if it refuses `.` scaffold to `bridge/app` and keep the folder). Inspect generated `.env` names; map to CONTRACTS env (`SPECTRUM_PROJECT_ID/SECRET`). Replace the echo handler: on inbound, POST to `${PP_BACKEND_URL}/api/inbound` with header `X-PP-Bridge-Token`, body `InboundMessage` (provider ids, space id, masked sender, raw text, received_at). Add `POST /send` (Bun.serve on 3001) that refuses any recipient != `PP_TEST_RECIPIENT`, sends via SDK (`space.send` on the DM space for the recipient; find the create-DM call in spectrum-ts iMessage provider docs: photon.codes/docs/spectrum-ts/providers/imessage and connection/routing page), returns `provider_message_id`. Dedupe inbound by `message.id`.
- First proof (before any backend): `bun start`, text the line from the owner's phone, get the echo. Then prove outbound: `curl -X POST localhost:3001/send ...` -> message arrives on the phone. Record both in INTEGRATION-FINDINGS with timestamps and provider ids (no phone number).
- Acceptance (FR-10, FR-11, T14, T29): real outbound to allowlisted handle only; inbound forwarded once even if delivered twice (replay the same payload twice -> backend returns `duplicate: true`); non-allowlisted recipient -> 403 in both bridge and backend.
- Verify: `bun test` in bridge (allowlist + dedupe unit tests); manual round trip with screenshot of the phone (E will mask).
- Fallback: if iMessage enrollment is blocked after 20 minutes, switch provider to Telegram in the same SDK (owner installs Telegram, still a real text to the owner's phone, labeled "Telegram"). Never present `FakeMessaging` as live.
- Stop: no provider works by 1:40 PM -> escalate to lead; demo narrative switches to labeled fallback.

### C-02 Band product handoff via CLI (P0) — 30 min
- Steps: `backend/payrollpilot/band/cli.py`: wrapper over `~/.local/bin/band` (`onboard --host generic --name pp-audit|pp-resolution|pp-payroll --json`, `chat new`/`add` for room `PayrollPilot Cases`, `send --body-file`, `inbox`, `ack`, `reply`, `ask --prompt`, `work` board items). Verify each command with `--help` and one real call; record which exist. Wire `POST /api/exceptions/{id}/handoff`: coordinator transition + `pp-audit` posts a minimized case card (id, category, title, stage impact; no names/amounts beyond cents of the exception) and creates a `band work` item; `pp-resolution` acks (`handoff.accepted`). On approval requests, `band ask --prompt "Approve sending batch X (hash ...)?"` so the human decision appears in Band; the answer is recorded as an `Approval` only through the backend route (the UI click or the Band answer both call `POST /api/approvals`). Payroll Prep receives the applied correction as a room message + work item moved to done.
- Acceptance (FR-29, S2 brief): room shows 3 agent participants, work items moving, one human decision; `band usage` shows tokens/cost per local agent (capture for E). Delete test: with `PP_BAND_ENABLED=0` the handoff route returns `503 band_required` and the case cannot move to Resolution.
- Verify: `backend/.venv/bin/pytest -q backend/tests/test_c02_band.py` (mocks subprocess) + one real run with screenshots of the Band room, board, and usage view.
- Fallback: if generic-host agents cannot post, use `band room send` as the account owner with an `[pp-audit]` prefix and document the limitation honestly; still require Band for the transition.

### C-03 Cognee write + recall that changes an action (P0) — 30 min
- Steps: `backend/.venv/bin/pip install cognee`; env per `.env.example` (custom provider via OpenRouter, fastembed embeddings). `memory/cognee_memory.py`: `write_resolution(res)` -> `cognee.remember(text, dataset "pilotco_cases")` where text is a scoped sentence ("Resolution res_01, cycle cyc_x: time entry te_0001 belongs to job_02 (off-site child of job_01); confirmed by owner test reply on <date>; evidence src ids ..."); `recall(scope) -> hits` using `cognee.recall(query_text, datasets=["pilotco_cases"], query_type=SearchType.CHUNKS or GRAPH_COMPLETION)`. `memory/apply.py`: validates hit references against current records (ids exist, cycle matches) before returning `next_action_after`. `POST /api/memory/recall-check`.
- Proof (T15): process 1 writes; kill it; process 2 (fresh uvicorn, or `python -m payrollpilot.memory.demo_recall`) recalls and changes `next_action` for the later disposal-receipt case from `ask ops lead which job` to `propose allocation to job_02 pending owner approval`. With Cognee disabled, the same case stays `insufficient_evidence` and asks again.
- Acceptance (FR-15, FR-29, T15, T29): recall hit includes evidence refs; no approval is created by recall; delete test passes.
- Verify: `backend/.venv/bin/pytest -q backend/tests/test_c03_memory.py` (unit with fake) + real run log pasted into INTEGRATION-FINDINGS (query, hit text, before/after action).
- Fallback: if OpenRouter via `custom` fails for graph extraction, set `LLM_MODEL=openrouter/openai/gpt-5.4-nano` or use `CHUNKS` search only (embeddings only, no LLM). Never replace with SQLite.

### C-04 Product agents on OpenRouter (P0) — 30 min, after C-01 first proof
- `agents/llm.py`: httpx client to `https://openrouter.ai/api/v1/chat/completions` with tools + `response_format` JSON schema; usage + cost recorded on each event; budget stop at `PP_MODEL_BUDGET_USD`. `agents/resolution.py`: `draft_batch(exceptions) -> MessageBatch text` (template skeleton + model wording; must include dates, durations, job refs), `parse_reply(inbound, batch) -> ParsedReply` (haiku; schema-validated; vague "yes" to multiple questions -> `ambiguous` for all; instruction-like content -> `blocked.unauthorized_instruction` event and no answers), `draft_clarification`. `agents/audit.py`: investigation note + respondent proposal only. `agents/payroll.py`: calls core, requests owner decision.
- Acceptance (FR-09, FR-11, FR-12, FR-17 part, T14, T17): `replies_v1.json` cases produce the expected statuses; clarification stays within the batch's recipient and exception ids; budget exhaustion yields `budget.exhausted` and a paused state.
- Verify: `backend/.venv/bin/pytest -q backend/tests/test_c04_agents.py` (recorded responses) + one live call log.

### C-05 Routes: draft, send, inbound, clarify (P0) — 20 min, after C-01 + A-02
- Implement CONTRACTS routes; `send` requires `permissions.check_send`; `inbound` dedupes, stores raw text, parses, updates exception states via coordinator, emits events; `clarify` drafts a bounded follow-up (new batch, needs new approval).
- Verify: `backend/.venv/bin/pytest -q backend/tests/test_c05_routes.py`; live G1 run with D's UI.

## Status log

```
LANE C status @ 12:45
Done: C-03 (acceptance: write in process 1, fresh process 2 recall changed next_action, approval_created false, --no-memory control stays insufficient_evidence)
In progress: C-01 bridge built, live round trip blocked on Photon credentials
Changed files: bridge/*, backend/payrollpilot/memory/*, backend/tests/test_c03_memory.py, INTEGRATION-FINDINGS.md
Tests run: cd bridge && bun test -> 9 pass, 0 fail; backend/.venv/bin/python -m pytest -q backend/tests/test_c03_memory.py -> 7 passed
Evidence: INTEGRATION-FINDINGS Cognee row (pids 15644 write, 17143 recall, 17251 control)
Blockers: Photon phone + project credentials in bridge/.env; PP_TEST_RECIPIENT; OPENROUTER_API_KEY for C-04
Next: C-02 Band product handoff
Handoff requested: A adds app.include_router(routes_comms.router) and cognee/fastembed/python-dotenv to backend deps
```

```
LANE C status @ 12:50
Done: C-03; C-02 agent handoff + board (acceptance: 3 agent participants, audit->resolution->payroll messages, task #2 pending->in_progress->completed). Human decision posted, owner reply pending.
Changed files: backend/payrollpilot/band/*, backend/tests/test_c02_band.py, INTEGRATION-FINDINGS.md
Tests run: backend/.venv/bin/python -m pytest -q backend/tests/test_c02_band.py -> 7 passed
Evidence: INTEGRATION-FINDINGS Band (product handoff) row; room a55619f6-19f6-4504-881f-a6d5b5d2ce4d
Blockers: band ask unsupported for generic peers (fallback: room message + inbox reply); owner must reply "approve msg_batch_spike02" in the room
Next: C-04 agents (template path now, live OpenRouter once key lands)
Handoff requested: A: backend startup calls band.ensure_peers(os.getpid()) when PP_BAND_ENABLED=1; env PP_BAND_ROOM_ID
```

```
LANE C status @ 12:55
Done: C-03 (merged #8), C-02 agent handoff (PR #12), C-04 agents (tests with stub transport; live call pending key), C-05 routes (tests with fake messaging + fake band)
Changed files: backend/payrollpilot/agents/*, backend/payrollpilot/routes_comms.py, backend/tests/test_c04_agents.py, backend/tests/test_c05_routes.py
Tests run: backend/.venv/bin/python -m pytest -q -> 61 passed, 1 skipped, 1 failed (lane A test_health_reports_comms_routes_absent now sees "loaded"); bridge bun test -> 9 pass
Evidence: INTEGRATION-FINDINGS lane C notes 1:05 PM
Blockers: Photon credentials + PP_TEST_RECIPIENT (C-01 live), OPENROUTER_API_KEY (C-04 live), owner reply in Band room (human decision)
Next: live C-01 round trip and G1 run as soon as credentials land
Handoff requested: A: update test_health_reports_comms_routes_absent to "loaded"; state.py use payrollpilot.memory.cognee_memory.CogneeMemory when PP_MEMORY=cognee and payrollpilot.band.CliBand when PP_BAND_ENABLED=1 (routes_comms already does this itself); health integrations photon/band/cognee from INTEGRATION-FINDINGS
```

```
LANE C status @ 13:37 Pacific (C-06 continuation)
Done: read handoff + integration ledger; verified healthy existing services and real comms adapter selection; captured live Cognee baseline (3 hits rejected, action unchanged, approval_created false).
In progress: owner-gated correction and clarification loop; final recall comparison and evidence PR.
Changed files: INTEGRATION-FINDINGS.md; docs/plans/C-communication-agents.md (status only).
Tests run: GET /api/health -> ok true; GET /api/comms/health -> cognee/band_cli/bridge; POST /api/memory/recall-check -> applied false, approval_created false. No unit tests run for evidence-only notes.
Evidence: evt_71d97efa4a7f at 2026-10-20T13:37:50-07:00; corr_a647520203 proposed; msg_batch_53be61bf427b draft.
Blockers: owner must approve/apply corr_a647520203 in UI, then approve clarification in Band and reply on phone.
Next: confirm correction application, give the next owner step, capture clarification provider/inbound/resolution/memory ids, repeat identical recall request.
Handoff requested: owner UI decision; final PR after the loop has evidence. Generic health adapter labels disagree with GET /api/comms/health (recorded in integration ledger).
```
