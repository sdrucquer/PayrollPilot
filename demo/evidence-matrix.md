# Evidence matrix (v2, 2026-10-20 1:00 PM)

Status values: **captured** (file path required), **pending**, **unavailable** (with the honest reason), **cut** (beat removed from the film). A row may say captured only with a path under `demo/evidence/` (sanitized, committed) or `demo/evidence/private/` (raw, gitignored; the sanitized copy is what the film uses). Source of truth for "proven" is `INTEGRATION-FINDINGS.md` on main plus the lane's Status log; lane E copies, never upgrades.

Requirement sources: PRD FR-29 (product agents coordinate through Band with a human decision; Cognee memory recalled across restart), FR-30 (demo shows real vs synthetic honestly), FR-31 (every integration claim backed by captured evidence); sponsor brief items for Band and Cognee; owner's hard requirements for the video.

| Row | Claim | Requirement | Evidence artifact (path) | Status | Captures | Film beat |
|---|---|---|---|---|---|---|
| R01 | Stage 1 wages and each Stage 2 item have separate readiness; no roll-up to "complete" | FR-24, FR-27, T22, T24 | `demo/evidence/screens/d01-board-1280.png`; `demo/evidence/screens/board.png`, footage `s1-board.mov` | partial: D-01 board on placeholder data | D screenshot, owner clip | 1 |
| R02 | Agents have different tool allowlists; coordinator owns state and approvals | ARCH 3, AGENTS | test output from C-04/F-02 in `demo/evidence/logs/agents-permissions.txt` | pending | C, F | how-it-works |
| R03 | Band: 2+ product-agent participants in one room (pp-audit, pp-resolution, pp-payroll) | Band brief, FR-29 | `demo/evidence/band/handoff-run.txt`; `demo/evidence/band/room.png`, `s2b-band-room.mov` | captured (CLI proof); Band Desktop screenshot pending | C | 2 |
| R04 | Band: shared board, dependent handoff Audit -> Resolution -> Payroll Prep | Band brief, FR-29 | `demo/evidence/band/handoff-run.txt`; `demo/evidence/band/board.png`, handoff event log `demo/evidence/logs/handoff-events.json` | captured (CLI proof); Band Desktop screenshot pending | C | 2 |
| R05 | Band human decision: room `approve <batch_id>` reply | FR-29 | `demo/evidence/logs/live-flow-main27b.txt` | captured (main 1:32 report); Desktop footage pending | C report / owner clip | 2 |
| R06 | Approval binds exact text + recipient; changed text invalidates | FR-23, T16 | F-02 test output `demo/evidence/logs/safety-suite.txt`; dialog `demo/evidence/screens/approval-dialog.png` | pending | F, D | 3 |
| R07 | Only the allowlisted test recipient can receive (backend + bridge) | FR-10, FR-26, T29 | bridge + backend 403 test output `demo/evidence/logs/allowlist.txt` | pending | C, F | 3 |
| R08 | Real outbound iMessage to allowlisted owner | round trip | `demo/evidence/logs/live-flow-main27b.txt` | captured (main report); phone footage pending | C report / owner clip | 3 |
| R09 | Inbound test reply correlated to approved batch | FR-11 | `demo/evidence/logs/live-flow-main27b.txt` | captured (main 1:32 report); footage pending | C report / owner clip | 4 |
| R10 | Vague reply -> per-question ambiguous -> bounded clarification needing new approval | FR-12, T14 | `demo/evidence/screens/ambiguous.png`, C-04 test output | pending | C, D | 4 |
| R11 | Approved local correction: wages delta 0, job costing changes, only affected readiness changes | T02, FR-16 | `demo/evidence/screens/correction.png`, `readiness.changed` event in `demo/evidence/logs/recalc-events.json` | pending | A, B, D | 5 |
| R12 | Source record never written; source write and submit gated | safety 4, AGENTS | gated-action test output in `demo/evidence/logs/safety-suite.txt` | pending | F | 5, 7 |
| R13 | Cognee write of a scoped resolution | Cognee brief, FR-15 | `demo/evidence/cognee/recall-run.txt`; `memory.written` event + Cognee dataset name in `demo/evidence/cognee/recall-run.txt` | captured (CLI proof) | C | 6 |
| R14 | Recall by a different / restarted agent | Cognee brief, FR-29, T15 | `demo/evidence/cognee/recall-run.txt`; same log: process 1 pid/time, process 2 pid/time, query, hit text | captured (CLI proof) | C | 6 |
| R15 | Recall changes next action; no approval created; disabled Cognee -> stays insufficient_evidence | Cognee brief, T15 | `demo/evidence/cognee/recall-run.txt`; same log: next_action before/after; delete-test output | captured (CLI proof); in-app clip pending | C | 6 |
| R16 | Review packet + workbook (12 ledgers + Sources), totals verified, `original_updated: false` | FR-22, FR-28, T28 | `demo/evidence/screens/workbook-panel.png`, `demo/evidence/screens/workbook-tabs.png` (no real names) | pending | B, D | 7 |
| R17 | Per-item Stage 2 blockers with codes (policy missing shown, not guessed) | FR-17 to FR-21, T09, T11 | `demo/evidence/screens/stage2-cards.png` | pending | B, D | 7 |
| R18 | Honest destination "Gusto: not prepared"; nothing submitted | safety 4, PRD | `demo/evidence/screens/destination.png` | pending | D | 7 |
| R19 | REQUIRED: Band Desktop per-agent sessions, tokens and estimated cost for the actual participating team | Mandatory brief visibility | `demo/evidence/band/native-usage-status.txt`; `demo/mandatory-band-capture.md` | REQUIRED GAP: only unattributed usage found; no product-agent session rows; app events do not substitute | C validates native bindings; owner captures Desktop | e3 native Band cost view |
| R20 | Every on-screen element labeled real/cached/synthetic/seeded/test/playback/illustration | FR-30, safety 7 | the film itself + `demo/redaction-checklist.md` pass recorded in this file | pending | E, owner | all |
| R21 | Synthetic film; real Jobber read has partial coverage | A-03 | `demo/evidence/logs/live-flow-main27b.txt` | partial real read report; no complete coverage or final footage claim | A report / E labels | 1 |
| R22 | Shared room lead plan, claimed board work, routed @handoff and human Band decision, tied to actual participating team | Mandatory Band brief | `demo/mandatory-band-capture.md`; existing handoff/live-flow notes | partial: C reports real plan/board/handoff/decision; redacted capture guide `demo/evidence/band/mandatory-capture-references.md`; exact internal identifiers stay private; Desktop footage/mention-chip checks pending | C/lead facts; owner footage | m2/e2 |

## Capture log (append, newest last)

| Time | Row | Path | From | Note |
|---|---|---|---|---|
| 12:58 | R13-R15 | demo/evidence/cognee/recall-run.txt | INTEGRATION-FINDINGS (main), lane C C-03 | Cross-process CLI recall, CHUNKS search, GLiNER extraction (no LLM). In-app recall after a live reply not yet shown. |
| 12:58 | R01 | demo/evidence/screens/d01-board-1280.png | lane D PR 5 / main | Board on lane D placeholder data, before lane B fixtures and the one-screen redesign. Not final. |
| 13:00 | R03-R05, R19 | demo/evidence/band/handoff-run.txt | INTEGRATION-FINDINGS (main), lane C C-02 | Handoff + board tested via CLI; owner decision pending; band ask unsupported; Band usage not per product agent. Script line 07 changed accordingly. |

## Light draft refresh (2026-10-20)

The 152-second draft uses the frozen light identity. No screen recording was made. All 14 unique product clips remain pending; static screenshot fallbacks were removed. The draft retains PLANNED / FOOTAGE PENDING labels, a draft watermark, placeholder voice and pending integration rows. CLI evidence does not establish that product footage was captured. Owner must supply real running-app, Band and Cognee views; prior takes must say PLAYBACK.

## Mandatory brief correction

The cost/session/token view is required Band Desktop evidence. R19 is a REQUIRED GAP, not optional or satisfied by app OpenRouter events. Use `demo/mandatory-band-capture.md` B1–B6/C1–C4 acceptance and capture order. Codex chat coordination alone does not establish Band team coordination.

## Automatic capture and completed current-flow update

Owner superseded human recording: dedicated capture chat owns numbered `demo/film/clips/` on `cloud/film`, committed by **3:00 PM Pacific**. Owner only phone replies/foregrounding Band; E imports and renders. Current-flow behavior-changing recall, owner application and verified workbook are now evidenced by main C-07; full-response/cross-process evidence is tracked in PR #38. The identical-baseline-query timeout/500 attempts are not claimed successful. Media capture remains distinct from runtime proof. R19 native cost attribution remains REQUIRED GAP.
