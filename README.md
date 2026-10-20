# PayrollPilot

**From missing information to payroll-ready. With you in control.**

PayrollPilot prepares payroll for one home-service business. It detects time and cost exceptions with source evidence, groups questions for owner-approved messaging, interprets replies, proposes local corrections, and recalculates wages and job costs after approval. It shows readiness separately for employee wages and each quote commission, tips, and manager-pool item, then exports a 12-ledger review workbook. [Product scope](docs/PRODUCT-STATEMENT.md).

PayrollPilot never submits payroll, creates a Gusto draft, or writes to Jobber, Gusto, or QuickBooks. Missing inputs remain named blockers. The destination stays **Gusto: not prepared**.

## Demo evidence and labels

The current 2:32 light-identity film is a **draft**, with placeholder voice and 14 missing product clips. Product slots say **PLANNED / FOOTAGE PENDING**. The owner records the real running app, Band, and Cognee views; static design mockups and fixture screenshots cannot substitute for that footage. Nothing has been submitted.

| Element | What viewers may infer |
|---|---|
| Pay-period records | **SYNTHETIC**, de-identified Pilot Co / Worker A–D; seeded issues labeled separately. Film uses the fixture; partial real-read evidence is described below. |
| Real integration | **REAL** only when backed by the linked evidence; a running UI alone does not prove a provider round trip. |
| Owner answering as Ops lead | **TEST REPLY**, including replies sent through a real provider. Simulated fixture replies cannot prove iMessage. |
| Earlier recorded take | **PLAYBACK**, with data and reply provenance retained. |
| Story / architecture scenes | **ILLUSTRATION**, distinct from product footage. |

The [evidence matrix](demo/evidence-matrix.md) tracks capture status, including pending items. [Film instructions](demo/film/README.md), [shot list](demo/shot-list.md), [reply script](demo/reply-script.md), and [redaction checklist](demo/redaction-checklist.md) guide the owner’s recording.

## Integration status

This is an evidence snapshot from `origin/main` at `bcb5251` (live findings introduced at `27b40ae`) and existing sanitized Lane C artifacts, not a claim that the final film shows these results. [INTEGRATION-FINDINGS.md](INTEGRATION-FINDINGS.md) remains the source ledger; its dated notes supersede earlier table entries.

| Integration | Reported proof and remaining gap | Evidence |
|---|---|---|
| Band | Handoff and board tested at 12:47; owner room `approve <batch_id>` produced version-bound approval at 1:32. `band ask` unsupported for generic peers; product usage comes from app events. Desktop footage pending. | [R03–R05 / R19](demo/evidence-matrix.md), [latest live report](demo/evidence/logs/live-flow-main27b.txt) |
| Cognee | Scoped fact written and recalled by a fresh process; recall changed the proposed next action without creating approval. Local CHUNKS search / GLiNER; no graph-completion claim. In-app footage pending. | [R13–R15](demo/evidence-matrix.md), [cross-process proof](demo/evidence/cognee/recall-run.txt) |
| Photon iMessage | Real allowlisted round trip 1:12–1:14; 1:32 owner-approved batch, correlated TEST REPLY and live parsing. Final phone/app footage pending. | [R07–R09](demo/evidence-matrix.md), [main report](demo/evidence/logs/live-flow-main27b.txt) |
| OpenRouter | Main reports live strict-schema parse at 1:09 and 1:32, with usage recorded; vague/injected replies handled by deterministic guards. Final usage clip pending. | [main report](demo/evidence/logs/live-flow-main27b.txt), R10 / R19 |
| Browser Use / Jobber | Real read, **partial coverage**: 58 time entries, 10 workers, 13 jobs. Totals, source ids and approval state unverified; rates/payroll/payments/expenses not read. Film stays synthetic. | [R21](demo/evidence-matrix.md), [coverage report](demo/evidence/logs/live-flow-main27b.txt) |
| Gusto draft / source writes / submission | Unavailable; no executor. | [scope boundaries](docs/PRODUCT-STATEMENT.md) |

## Architecture and local run

The hackathon stack is already running under lane C. Leave backend :8000 and bridge :3001 running; the startup commands below are for a fresh checkout, not the recording session.

Three product agents propose actions with different permissions: Audit finds issues, Resolution asks and interprets, and Payroll Preparation computes and reports. A deterministic coordinator owns state and approvals in SQLite. FastAPI serves the React/Vite app; the Bun bridge connects messaging, with Band and Cognee adapters. [Architecture](ARCHITECTURE.md), [contracts](docs/contracts/CONTRACTS.md), [public brief](docs/PRODUCT-BRIEF.md).

Requirements: Python 3.13+, Node 22, Bun, and macOS for the local messaging setup. From the repository root:

```bash
cp .env.example backend/.env
cp bridge/.env.example bridge/.env
npm ci --prefix web
(cd bridge && bun install)
scripts/dev.sh
```

The script creates the backend virtual environment and installs backend/core packages, then starts backend `:8000`, bridge `:3001`, and web `:5173`. Configure local env files before enabling providers. Relevant names: `OPENROUTER_API_KEY`, `PP_MODEL`, `PP_MODEL_CHEAP`; Cognee `LLM_*` / `EMBEDDING_*`; Photon `SPECTRUM_PROJECT_ID`, `SPECTRUM_PROJECT_SECRET`; shared `PP_BRIDGE_TOKEN` and `PP_TEST_RECIPIENT`; `PP_BAND_ENABLED` / `PP_BAND_ROOM`. Use `.env.example` and `bridge/.env.example` for the full list. Never commit values. Optional Browser Use credentials do not establish a real-read proof.

```bash
curl -fsS http://127.0.0.1:8000/api/comms/health
curl -fsS http://127.0.0.1:8000/api/health
scripts/smoke.sh
```

Inspect `/api/comms/health` for active adapters and UI provenance. The older `/api/health` registry can disagree; lane C interprets discrepancies. Leave backend :8000 and bridge :3001 running; lane C controls case preparation. Fixture mode and fake adapters are development aids. These are operator instructions; Lane E did not run or validate the application in this documentation pass.

## Control boundaries

The owner approves the exact message and recipient, then separately approves proposed corrections. Changed content requires a new approval. Only the allowlisted test recipient can receive messages. Unknown money or time stays unknown; missing policy never becomes a guessed default. Replies and recalled facts cannot grant permission. Readiness stays scoped to wages and each compensation item.

## Submission and team

[Copy-ready submission and upload runbook](demo/submission.md). Feature freeze **2:45 PM Pacific**, owner recording **2:45–3:15**, upload **by 3:15**, deadline **3:30 PM**, October 20, 2026.

**Shanin Drucquer**
