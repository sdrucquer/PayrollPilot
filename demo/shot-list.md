# Shot list (v2, 2026-10-20 12:58 PM)

UI note: per `docs/UI-ONE-SCREEN.md` the app is one evolving screen with three zones (progress strip on top, "what's limiting payroll" list on the left, selected-blocker panel on the right). Route names below are replaced by zones; the film shows one frame that changes. Film visual register follows `docs/DESIGN-DIRECTION.md` (particle title mark on black; glass panels for product).

Two kinds of material, never mixed in one frame without a label:

- **Motion graphics** (ILLUSTRATION): rendered by `demo/film/` (Remotion). Lane E produces these; no product data is faked in them.
- **Product footage**: screen and phone recordings of the real running app, Band Desktop, terminal. The owner records these (lane E prepares the steps in `recording-setup.md`). Clips are dropped into `demo/film/public/footage/` (gitignored) with the names below; the film composites them full-frame with a provenance chip.

Capture format for every screen clip: QuickTime "Record Selected Portion" of the browser window at 1440x900 (or the app window), 30 fps, browser zoom 110%, dark mode, bookmarks bar hidden. Phone: QuickTime "New Movie Recording" with the iPhone selected as camera (USB), portrait, Do Not Disturb on, only the PayrollPilot thread open.

| # | Time | Source | What must be on screen | File name in footage/ | Provenance chip | Owner of proof |
|---|---|---|---|---|---|---|
| S0 | 0:00-0:51 | Remotion | Cold open, montage, turn, logo, "how it works" diagram | rendered | ILLUSTRATION | E |
| S1 | 0:51-1:05 | App, zone 1 strip + zone 2 | Progress strip (Collect -> Audit -> Resolve -> Prepare -> Review with the agent on each step), company label "Pilot Co", period, timezone, coverage chips with method, Stage 1 card, Stage 2 cards (Quote/marketing, Tips, Manager pool) each with readiness + blocker codes, destination badge "not prepared", health strip (Messaging / Memory / Band modes) | `s1-board.mov` | SYNTHETIC fixture (or REAL read) | D (UI), A (data) |
| S2a | 1:05-1:12 | App, zone 2 row -> zone 3 panel | Seeded issue "Already-paid shift on 2026-10-01 is on Job 01 but scheduled on Job 02": observed vs expected, evidence refs, stage impact `stage1_wages: none / stage2_costs: job_costing`, owner_agent audit; click Hand off; owner_agent becomes resolution | `s2a-handoff.mov` | SEEDED ISSUE | D, C |
| S2b | 1:12-1:23 | Band Desktop | The PayrollPilot room (Band default title; rename is refused for the human): participants pp-audit, pp-resolution, pp-payroll, owner; case card and the accepted reply; work board task moving to Completed; the `[decision.requested]` message and the owner's reply (`band ask` is unsupported for generic peers) | `s2b-band-room.mov` | REAL · Band Desktop | C |
| S3a | 1:23-1:32 | App, zone 3 | Draft batch text (two questions: the Oct 1 shift's job, and which job Job 03's off-site disposal run belongs to); approval dialog: exact text, masked recipient `***-**NN`, linked exception ids, `target_version` hash; Approve + Send; batch state "sent", provider status | `s3a-approve-send.mov` | REAL · Photon | C, D |
| S3b | 1:32-1:40 | Phone | Message arrives in Messages (thread header must NOT show a number: save the Photon sender as contact "PayrollPilot" beforehand) | `s3b-phone-arrive.mov` | REAL · iMessage | Owner |
| S4a | 1:40-1:46 | Phone | Owner types and sends reply R1 (vague "yes") from `reply-script.md` | `s4a-phone-vague.mov` | TEST REPLY | Owner |
| S4b | 1:46-1:55 | App zone 3 + phone | Inbound labeled TEST REPLY; per-question "ambiguous"; Clarify; approval of the follow-up; phone shows clarification and R2 clear reply; UI "answered", extracted job, quote | `s4b-clarify.mov` | REAL transport · TEST REPLY | C, D |
| S5 | 1:55-2:09 | App zone 3 then zone 1 | Proposed correction before/after; impact: wages delta $0.00, Job 02 labor delta; correction approval (kind local_correction); Apply; board: Stage 1 unchanged, one Stage 2 card changes | `s5-correction.mov` | REAL calc · SYNTHETIC data | A, B, D |
| S6a | 2:09-2:14 | Terminal | Backend stopped (Ctrl-C) and restarted; `date` printed before and after; no env values on screen | `s6a-restart.mov` | REAL | Owner / C |
| S6b | 2:14-2:26 | App, activity log under the strip (or recall-check output) | `memory.recalled` + `memory.applied` events by Payroll Prep; next_action before "ask ops lead which job" vs after "propose allocation to job_02 pending owner approval"; hit text with evidence refs; health strip "Memory: Cognee" | `s6b-cognee-recall.mov` | REAL · Cognee | C, D |
| S7a | 2:26-2:36 | App, Stage 1 expansion + Export workbook | Per-worker packet table; Export workbook toast -> sheets list, verified totals, draft version equal to packet, `original_updated: false` + note; Stage 2 cards with blockers; "Gusto: not prepared" | `s7a-review.mov` | REAL workbook · SYNTHETIC data | B, D |
| S7b | 2:36-2:40 | Numbers/Excel | The generated xlsx: tab strip with all ledgers, one pending tab showing `status: pending — <blocker>` | `s7b-workbook.mov` | REAL file · SYNTHETIC data | Owner |
| S8 | 2:40-2:55 | Remotion | Status card (values from evidence-matrix.md), close card | rendered | ILLUSTRATION | E |
| B1 | optional | App activity log | Per-agent tokens/cost from PayrollPilot's own OpenRouter usage events (Band usage covers coding sessions only) | `b1-agent-usage.png` | REAL | C, D |

## Playback rule

If a live beat fails during the final recording, use the clip from the rehearsal recording of the same beat only if it was a genuine run, and set its chip to `PLAYBACK · genuine run at HH:MM`. Never re-enact a failed integration with the fake adapter and call it live.

## Never on screen

Photon dashboard; any `.env`; terminal history showing keys; real names; phone numbers (thread header, contact card, notification banners); real rates; private allocation percentages; Gusto/Jobber/QuickBooks pages with company identity; the Band room's unrelated chats. See `redaction-checklist.md`.
