# PayrollPilot architecture (hackathon build, 2026-10-20)

Smallest shape that satisfies the PRD loop, keeps money math deterministic, and leaves every integration swappable.

## 1. Processes

```
 owner's phone (iMessage) <-> Photon Spectrum cloud <-> bridge/ (Bun, spectrum-ts, :3001)
                                                            | POST /api/inbound  ^ POST /send
                                                            v                   |
 web/ (Vite+React, :5173) --/api proxy-->  backend/ (FastAPI, :8000) ---- SQLite (records + events)
                                              |        |        |
                                              |        |        +-- core/payrollpilot_core (pure audit, calc, readiness, workbook)
                                              |        +-- memory/ Cognee (local LanceDB/Kuzu/SQLite; LLM via OpenRouter; fastembed)
                                              +-- band/ CLI adapter (~/.local/bin/band send|ask|work) -> Band Desktop room "PayrollPilot Cases"
                                              +-- agents/ Audit, Resolution, PayrollPrep (OpenRouter chat completions w/ tools)
                                              +-- adapters/ browser_use (lane A, offline job: writes data/private/snapshots/*.json)
```

Why three processes: Cognee is Python-native; Photon's documented client is TypeScript; the UI is a static SPA. The bridge has no business logic. If lane C finds a documented REST send endpoint on `spectrum.photon.codes`, the bridge can shrink to inbound-only or disappear without contract changes.

## 2. Data flow (the required loop)

1. **Load**: `POST /api/cycles/load` reads a snapshot (`docs/contracts/fixtures/cycle_synthetic_v1.json` or `data/private/snapshots/<name>.json`, produced by Browser Use / owner export). Snapshot records keep `source_ref`, `captured_at`, `version_hash`, and `SourceCoverage` rows. Stored as immutable records.
2. **Audit**: `POST /api/cycles/{id}/audit` calls `core.run_audit(snapshot)` (deterministic rules: missing job, long shift, open timer, overlap, duplicate, unassigned, identity, rate unconfirmed, already-paid allocation, cost duplicates/conflicts, coverage gaps). Exceptions stored with evidence and `stage_impact`. The Audit agent (LLM) may add an investigation note and propose respondent; it cannot create money facts.
3. **Handoff**: `POST /api/exceptions/{id}/handoff` moves the case to Resolution: coordinator changes `owner_agent`, emits `handoff.requested`, and (when `PP_BAND_ENABLED=1`) posts to the Band room as the `pp-audit` peer; `pp-resolution` acknowledges (`band ack`/`reply`) and emits `handoff.accepted`. Band carries coordination; SQLite carries state.
4. **Draft question**: Resolution agent groups exceptions by respondent, drafts the text (schema-validated), creates `MessageBatch` (draft, `text_hash`). UI shows exact recipient (masked), text, linked issues.
5. **Approve + send**: owner creates `Approval(kind=message_send, target_version=text_hash)`. `POST /messages/{id}/send` -> `permissions.check_send` (allowlist + version) -> bridge `/send` -> Photon -> owner's phone. `message.sent` event with provider id. Human decision also surfaced via `band ask` when enabled.
6. **Reply**: Photon -> bridge (`app.messages` stream or signed webhook) -> `POST /api/inbound` (bridge token). Dedupe on `provider_message_id`. Resolution agent parses into `ParsedReply` per exception (answered/partial/ambiguous/conflicting/unaddressed). Unclear items stay open; `clarify` drafts a bounded follow-up (same recipient, same exception scope) that again needs approval. Instruction-like text (T17) -> `blocked.unauthorized_instruction`, no action.
7. **Resolve + correct**: answered facts become a `Resolution` (actual confirmer = owner test phone; intended = ops lead). Resolution writes a scoped memory to Cognee (`memory.written`). If a calculation changes, a `LocalCorrection` is proposed with before/after and impact; it needs `Approval(kind=local_correction)`. Source records are never written.
8. **Recalculate**: `apply` reruns `run_audit` on the corrected view, recomputes `Readiness` for Stage 1 and each Stage 2 item via `core`, emits `readiness.changed` only for affected items. T02 shows wages unchanged, job costing changed.
9. **Memory recall**: Payroll Preparation (or a restarted process) calls `memory.recall(scope)` before evaluating a related item (e.g., a later disposal receipt on the off-site child job). A hit is validated against current record IDs, then changes `next_action` (`memory.applied`). Without Cognee the item stays `insufficient_evidence` and asks again. `/api/memory/recall-check` returns before/after for the demo and T15.
10. **Packet + workbook**: `GET /packet` builds the internal review packet; `POST /workbook` writes an xlsx with all 12 ledgers (pending tabs present), reopens it, verifies totals equal the packet's draft version, stores `WorkbookArtifact` with `original_updated: false` unless the owner supplied the designated workbook and authorized an update (not in the default demo). Destination stays `internal_draft`.

## 3. Agent layers

- **Development agents**: Claude Code / Codex sessions (lanes A-F) building this repo; coordinated via Band Desktop once the Claude Code plugin works, else via PRs and the owner.
- **Product agents** (`backend/payrollpilot/agents/`): three roles over one model (`PP_MODEL`), each with a tool allowlist:
  - Audit: `read_snapshot`, `run_checks`, `propose_respondent`, `request_handoff`.
  - Resolution: `draft_batch`, `parse_reply`, `draft_clarification`, `record_resolution`, `memory_write`, `memory_recall`.
  - Payroll Prep: `compute_readiness`, `build_packet`, `build_workbook`, `memory_recall`, `request_owner_decision`.
  The coordinator (`coordinator.py`) is plain code: it owns state transitions, approval checks, dedupe, budget (`PP_MODEL_BUDGET_USD`), and the stop flag. Agents return structured proposals; the coordinator applies or rejects them. A Band message, a memory, or a reply can never grant permission.

## 4. Persistence

SQLite file `backend/data/payrollpilot.db`. Tables: `records(kind, id, version, json, created_at)` (append new versions; latest view by `(kind,id) max(version)`), `events(id, at, cycle_id, actor, type, json)`, `approvals`, `inbound_dedupe(provider_message_id unique)`, `send_log(batch_id unique)`. Restart-safe by construction (T18). Cognee stores a copy of resolutions with `memory_ref` back to `res_` ids; it is never read for amounts.

## 5. Provider adapters and fallbacks

| Concern | Real adapter | Fallback (labeled in `/api/health` and UI) |
|---|---|---|
| Messaging | `BridgeMessaging` -> bridge -> Photon iMessage | `FakeMessaging` replays `replies_v1.json` (dev only; never in the demo as "live") |
| Memory | `CogneeMemory` | `InMemoryMemory` (dev only; demo requires Cognee) |
| Coordination | `CliBand` (shells `band`) | `NullBand` (events only; demo requires Band) |
| Model | OpenRouter `PP_MODEL` | Switch model id via env; agents degrade to deterministic drafts (templates) if budget exhausted |
| Source data | Browser Use snapshot / owner export | Synthetic fixture, `provenance: synthetic` |

## 6. Approval enforcement

`permissions.py` exposes `check_send(batch, approval)`, `check_apply(correction, approval)`, `check_recipient(handle)`, `assert_not_gated(action)`. Routes call these; agents cannot. Approvals bind to content hashes; any change invalidates (`approval.invalidated` event). `source_write` and `payroll_draft` kinds exist in the schema for later gates but have no executor.

## 7. Workbook

`core/payrollpilot_core/workbook.py` builds sheets: Review, Labor, Time, Manual payments, Payments, Expenses, Overhead, Quotes/marketing, Tips, Questions, Job queue, Carry-forward, plus `Sources` (snapshot ids, versions, calc version). Pending ledgers contain a header row and a `status: pending — <blocker>` row. The builder reopens the file and asserts totals against the packet before returning.

## 8. Non-goals (not built)

Gusto draft creation, source writes, crew texting, multi-tenant, billing, Snyk/Flexprice, hosting. Each appears in the UI as "not prepared / gated" where the PRD requires an honest label.
