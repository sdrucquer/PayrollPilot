# PayrollPilot

**Your AI payroll team. From missing information to payroll-ready—with you in control.**

Payroll is rarely blocked by arithmetic. It is blocked by the person who knows which job a shift belonged to, the unexplained expense, and the answer buried in a text thread. PayrollPilot turns that chase into a coordinated workflow: **find the exception → ask the right person → remember the answer → propose the correction → get owner approval → prepare the review.**

[**Watch the 2:35 demo**](https://github.com/sdrucquer/PayrollPilot/blob/main/demo/video-out/payrollpilot-demo.mp4) · [**Try the interactive preview**](https://vercel-stage-delta.vercel.app) · [Architecture](ARCHITECTURE.md) · [Evidence ledger](INTEGRATION-FINDINGS.md)

The hosted preview is explicitly labeled **synthetic, browser-local simulation; no texts leave the app**. The film combines real local integration captures with clearly labeled illustrations and earlier evidence. [Exactly what is real in each scene](demo/video-out/README.md).

## A team that closes the loop

Three product agents share one case, one plan and a Band room. They have different tools and permissions; a deterministic coordinator owns state and approvals.

| Agent | Owns | Handoff |
|---|---|---|
| **Audit — `pp-audit`** | Finds missing jobs, long/overlapping/duplicate time and cost exceptions; attaches evidence and stage impact. | Directly @mentions Resolution and opens a board item. |
| **Resolution — `pp-resolution`** | Claims the case, drafts grouped questions, interprets replies and proposes corrections. | Brings an exact message decision to the owner in Band; hands the applied result to Payroll Preparation. |
| **Payroll Preparation — `pp-payroll`** | Recalculates wages and job costs, checks scoped readiness and prepares the review workbook. | Acknowledges the result; the owner gets the review and remaining blockers. |

Development used Claude Code and Codex sessions in separate lanes, reviewed PRs and lead integration. These coding sessions are distinct from the three product agents; a combined coding-harness Band view was not captured.

### The demonstrated payoff

In the verified local case, the owner approved moving a shift from Job 01 to Job 02. **Employee wages changed by $0; job labor cost moved by $200.** PayrollPilot preserved that distinction, recalculated readiness and generated a verified review packet plus a **13-sheet workbook with 12 ledgers**. This correction was applied earlier today; the film labels it accordingly.

A confirmed off-site job relationship was written to **Cognee Open Source**. A later recall changed the next action from **“ask the Ops lead which job”** to **“propose allocation to Job 02, pending owner approval.”** Recall created **no approval**. The system remembers a fact without turning memory into permission.

## Built for the judging criteria

| Criterion | What PayrollPilot demonstrates | Proof |
|---|---|---|
| **Band Desktop — 25%** | Three agents in a shared room, a posted plan, claimed work items, direct @handoffs, owner room approval and Payroll ACK. Current main requires Band coordination for new drafts/sends; deletion/failure tests block effects. | [Room/handoff](demo/film/clips/12-band-chat-handoff.png), [board](demo/film/clips/09-band-board.png), [plan](backend/payrollpilot/band/PRODUCT-ROOM-PLAN.md), [required-Band tests](backend/tests/test_c08_band_required.py) |
| **Cognee — 25%** | A fact written during the workflow survives a fresh process and changes the proposed next action, without approving anything. | [Cross-process proof](demo/evidence/cognee/recall-run.txt), [real recall response](demo/film/clips/10-cognee-recall.txt) |
| **Startup viability — 20%** | A concrete buyer: the owner of a home-service business who reconciles hours, job costs and missing answers before payroll. One review replaces scattered follow-ups. | [Product statement](docs/PRODUCT-STATEMENT.md), [public brief](docs/PRODUCT-BRIEF.md) |
| **Technical execution/demo — 20%** | Real approved iMessage send/reply, strict-schema interpretation, version-bound approvals, deterministic calculations, verified workbook export and a working labeled web preview. Latest lead suites: **144 core + 150 backend tests passed**. | [Rehearsal observation](tests/integration/REHEARSAL.md), [send capture](demo/film/clips/02-approve-and-send.mp4), [integration ledger](INTEGRATION-FINDINGS.md) |
| **Innovation — 10%** | Business memory changes the next question; wages and job allocation remain independent; agents propose while the owner controls effects. | [Core](core/payrollpilot_core), [memory](backend/payrollpilot/memory), [approval boundaries](backend/payrollpilot/permissions.py) |

**Evidence limits that matter to judging:** the native Band cost screenshot is real but **unattributed**; it does not establish per-product-agent costs. The board is a captured state, not filmed motion. Fresh ambiguous-reply/apply footage and the combined development-agent Band view are unavailable. These remain gaps in the mandatory demonstration, not claimed completions. [Full evidence matrix](demo/evidence-matrix.md).

**Snyk bonus:** a real, repeatable [frontend dependency scan](tests/security/snyk-web-summary.json) checked **8 production dependencies with no known vulnerable paths**, then **103 including development dependencies**. The broader scan found **one high-severity picomatch ReDoS issue through two Vite paths** (direct and via tinyglobby), with no patch/upgrade reported by Snyk. The finding remains open; this is not a clean whole-application audit. Reproduce with `scripts/f_snyk.sh` after Snyk authentication. The video predates this late scan.

**Business model:** a per-company subscription with metered extra processing is a proposal. Flexprice billing is not implemented or claimed.

## Real integrations, measurable boundaries

| Integration | Verified capability |
|---|---|
| **Band Desktop** | Product-room messages, direct handoffs, board ownership, owner approval and receiving-agent acknowledgements. Native room, board and usage screenshots captured. |
| **Cognee Open Source** | Working write/recall with a behavior change across a fresh process. CHUNKS retrieval; no graph-completion claim. |
| **Photon iMessage** | Real messages to the owner's allowlisted test phone, correlated replies and live parsing. Owner answers are labeled **TEST REPLY**. |
| **OpenRouter** | Model-assisted drafting/parsing with schemas, usage tracking and deterministic guards around effects. |
| **Browser Use / Jobber** | Read-only extraction: **58 entries, 58 verified source IDs, source total 58, 10 worker profiles, 12 actual jobs**. All 58 source approval states are unapproved. Per-entry URLs were not exposed. Rates, payroll, payments and expenses remain unread; this is partial payroll coverage. Private snapshots are excluded from the repository and hosted preview. |

The app shows readiness **separately for wages, quote commission, tips and manager pool**, with named blockers. Missing rates, identity matches and policy stay unresolved. PayrollPilot does **not** submit payroll, create a Gusto draft or write to source systems. The destination remains **Gusto: not prepared**.

## Why an owner can trust the workflow

- **Exact approval:** sends and corrections bind to the reviewed content/version. Changed content needs a new approval.
- **Bounded delivery:** only the allowlisted test recipient can receive a message; outbound and inbound deduplication prevent duplicate effects.
- **Deterministic money:** integer cents/minutes, Decimal arithmetic, no invented rates or policy; unknown stays unknown.
- **Evidence before action:** replies, source pages and recalled facts are data. None can grant permission or bypass the coordinator.
- **Visible provenance:** synthetic records, seeded issues, test replies, real captures and illustrations stay distinguishable.

## Run it locally

Python 3.13+, Node 22+, Bun, and macOS for the local messaging setup. For a **fresh checkout**:

```bash
cp .env.example backend/.env
cp bridge/.env.example bridge/.env
npm ci --prefix web
(cd bridge && bun install)
scripts/dev.sh
```

The script installs backend/core packages and starts FastAPI `:8000`, the bridge `:3001` and React/Vite `:5173`. Configure providers through the example env files; never commit values. `/api/comms/health` is authoritative for active messaging/Band/Cognee modes; the older `/api/health` adapter registry can disagree. **Leave the existing recording stack running.**

For the browser-only synthetic preview:

```bash
cd web
npm run dev:fixture
```

[Vercel services configuration](docs/VERCEL.md): public `web`, internal `backend`, imported `core` library. The hosted preview does not connect to the local messaging stack; full durable cloud hosting is separate work.

## Team and submission

**Shanin Drucquer** · built with Claude Code and Codex.

[Submission copy](demo/submission.md) · [Final film and provenance](demo/video-out/README.md) · [Contracts](docs/contracts/CONTRACTS.md).

Hackathon freeze tag: `v0.1-hackathon`. Post-freeze fixes and submission assets are on main. Nothing submits payroll on the owner's behalf.
