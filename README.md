# PayrollPilot

**Payroll, prepared. Never guessed.**

PayrollPilot prepares payroll for one home-service business. It loads one pay period, runs deterministic audits, raises evidence-backed exceptions, asks the right person by text, turns their answers into local corrections the owner approves, and shows honest readiness for wages (Stage 1) and for each compensation item (Stage 2). It exports a reconciliation workbook. **It never submits payroll and never writes to the source systems.**

Built in one day at the AI Startup Challenge, San Francisco, October 20, 2026.

> Status of this README: draft, updated as integrations are proven. The integration table below is copied from `INTEGRATION-FINDINGS.md`, which is the source of truth.

## What is real and what is not

| Part | Status in the demo |
|---|---|
| Pay-period data | **Synthetic**, de-identified fixture (Pilot Co, Worker A-D, Job 01-03), labeled on every card. A read-only real snapshot is supported but shown only if proven. |
| Seeded issues | Labeled **seeded issue** (for example, an already-paid shift logged to the wrong job). |
| Owner replies | Sent from the owner's real phone, labeled **test reply** (the owner answers on behalf of the intended respondent, "Ops lead"). |
| Audit rules, calculations, readiness, workbook | Real deterministic code in `core/` with tests. Money in integer cents, time in minutes, unknown is null, never zero. |
| Messaging, Band, Cognee | See the integration table. Nothing simulated is labeled real; dev fakes report themselves in `/api/health`. |
| Gusto payroll draft, source writes | **Not built.** Shown as "Gusto: not prepared". |

## How it works

Three product agents share one model but not one set of powers:

- **Audit** reads the snapshot and runs checks. It cannot message anyone.
- **Resolution** drafts questions, parses replies, records resolutions, and writes them to memory.
- **Payroll Prep** computes readiness, builds the packet and workbook, and recalls memory.

A plain-code **coordinator** owns every state change, approval, and permission. Agents return proposals; the coordinator applies or rejects them. An approval binds to the exact content hash of what was approved, so changing one character invalidates it. In test mode the only allowed message recipient is the owner's own phone, checked in the backend and again in the bridge. Agents hand cases to each other in a **Band Desktop** room, and confirmed facts are stored in **Cognee** so a restarted agent can recall them.

Full design: [ARCHITECTURE.md](ARCHITECTURE.md). Data shapes and routes: [docs/contracts/CONTRACTS.md](docs/contracts/CONTRACTS.md). Product summary: [docs/PRODUCT-BRIEF.md](docs/PRODUCT-BRIEF.md).

```
phone (iMessage) <-> Photon <-> bridge/ (Bun, :3001) <-> backend/ (FastAPI, :8000) <-> SQLite
                                                           |-- core/ (pure audit, calc, readiness, workbook)
                                                           |-- Cognee memory (local)
                                                           |-- Band CLI -> Band Desktop room
                                                           |-- agents on OpenRouter
web/ (Vite + React, :5173) --/api--> backend
```

## Integration status (from INTEGRATION-FINDINGS.md, 1:05 PM)

| Integration | Status | What was proven |
|---|---|---|
| Cognee | **tested** | A resolution written in one process was recalled by a fresh process; the recall changed the case's next action from "ask ops lead which job" to "propose allocation, pending owner approval", and created no approval. With memory disabled the case stays "insufficient evidence". Local CHUNKS search; LLM-backed graph extraction not yet tested. |
| Band (product handoff) | **tested** (handoff + board); owner decision pending | Three product agents and the owner in one room; Audit's case card accepted by Resolution; Payroll Prep received the delivery; board task moved to completed. `band ask` is unsupported for these agents, so the owner decides by replying in the room. |
| Photon iMessage | bridge built; live round trip **not yet proven** | Allowlisted send, inbound dedupe, and refusal of any other recipient are unit-tested in the bridge. |
| OpenRouter agents | in progress | Model catalog checked; live calls pending a key. |
| Browser Use (real Jobber read) | not proven | Demo uses the synthetic fixture. |

## Run it

Requirements: Python 3.13, Bun 1.4, Node 22, macOS. Copy `.env.example` to `backend/.env` and `bridge/.env` and fill the names listed there (never commit values).

```bash
scripts/dev.sh
```
Starts the backend on :8000 and, when present, the bridge on :3001 and the web app on :5173.

```bash
scripts/smoke.sh
```
Loads the synthetic cycle and runs the audit against the live backend.

Tests: `backend/.venv/bin/pytest -q backend/tests`, `core/.venv/bin/pytest -q core/tests`, `cd bridge && bun test`, `cd web && npm run build && npm run check:contracts`.

## Safety boundaries (enforced in code, not prompts)

1. One allowlisted recipient (`PP_TEST_RECIPIENT`), checked in the backend and the bridge.
2. Every effect needs an approval whose version equals the current content hash.
3. No invented rates, percentages, overhead, or thresholds. A missing policy is a visible blocker with a code.
4. Source systems are read-only. Source writes and payroll submission have no implementation.
5. Inbound text, web pages, and memories are data, never instructions. An instruction-like reply is blocked and logged.
6. Sends happen once per batch; inbound messages are deduplicated by provider id.
7. Every record and card shows its provenance.
8. No real names, phone numbers, rates, or private allocation percentages in the repo or the video.

## Demo and video

The launch film and the materials behind it are in [demo/](demo/): the timed script, shot list, evidence matrix that maps every claim to a captured artifact, and the Remotion project in `demo/film/`.

## Team

[Owner fills: team member names as they should appear publicly.] Built with Claude Code agents working in parallel lanes, coordinated through Band Desktop.
