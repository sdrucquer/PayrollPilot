# PayrollPilot film: timed script (v3, owner's cut, 2026-10-20 1:07 PM)

Structure is the owner's cut relayed by the lead at 1:05 PM, with the lead's edits: hook ~15 s, reveal ~10 s, the product ~75 s, under the hood ~35 s, close ~17 s. Runtime **2:32** (hard cap 3:00). It keeps every evidence requirement from `DEMO-PLAN.md` and claims nothing beyond the "It can" list in `docs/PRODUCT-STATEMENT.md`. The close states the "It cannot" boundary on screen: the owner approves every message and correction, and PayrollPilot never submits payroll.

Narration: 289 words, measured 103 s with the placeholder voice. Two recording paths, both on the same cue times: ElevenLabs (`demo/film/scripts/vo.mjs` with a key) or the owner's own voice (`demo/vo-read-script.md`).

Labels on screen: **ILLUSTRATION** (motion graphics, hook B-roll with fictional data, the architecture diagram, title and close cards), **REAL**, **SYNTHETIC**, **SEEDED ISSUE**, **TEST REPLY**, **PLAYBACK** (genuine earlier run), **DESIGN MOCKUP** (only if a lane G mockup is ever shown; not planned). A product segment with no footage yet renders a dashed "FOOTAGE PENDING" frame and a grey PLANNED chip.

| Time | Section | On screen (clip names in shot-list.md) | VO | Label |
|---|---|---|---|---|
| 0:00-0:15 | Hook | Fast cuts of fictional B-roll: timesheet with an open timer and a shift with no job, bank feed with uncategorized costs, 14 unread messages, a spreadsheet with #REF! and totals that differ. Slams: "Missing hours." "Unassigned expenses." "Numbers that don't add up." Freeze, desaturate. | h1-h4 | ILLUSTRATION · fictional data |
| 0:15-0:25 | Reveal | Music hit. Particle mark assembles on black; "PayrollPilot"; "Your AI-powered payroll operations team." | r1 | ILLUSTRATION |
| 0:25-0:35 | Product: Audit finds an issue | Running app: progress strip, Stage 1 and Stage 2 rows, then the seeded issue "Already-paid shift on 2026-10-01 is on Job 01 but scheduled on Job 02" (wages none, job costing). | m1 | SEEDED ISSUE · synthetic data |
| 0:35-0:42 | Product: Band handoff | Band Desktop: pp-audit posts the case card, pp-resolution accepts, board task moves. | m2 | REAL · Band Desktop |
| 0:42-0:48 | Product: approval | Zone 3: two questions (te_0014 job; Job 03 parent), masked recipient, linked issues, hash; Approve and send. | m3 | REAL |
| 0:48-0:54 | Product: real iMessage | Split: batch "sent" + phone receiving the message. | m3 | REAL · Photon iMessage · test mode |
| 0:54-1:03 | Product: vague reply | Phone "yes"; both questions ambiguous; Clarify drafts one follow-up; new approval; phone receives it. | m4 | TEST REPLY |
| 1:03-1:10 | Product: answer | Phone: clear answer. Zone 3: both answered (te_0014 -> job_02; Job 03 off-site for job_02), quote shown. | m5 | TEST REPLY |
| 1:10-1:21 | Product: correction | Correction before/after; impact wages $0.00, job labor moves to Job 02; Approve correction; Apply; only the affected item changes. | m6 | REAL calc · synthetic data |
| 1:21-1:32 | Product: Cognee in a separate process | Separate fresh recall process (timestamps), without touching live services; later disposal cost on Job 03; `memory.recalled`, `memory.applied`; next action "ask ops lead which job" -> "propose allocation to job_02 pending owner approval". | m7 | REAL · Cognee |
| 1:32-1:40 | Product: corrected review | Stage 1 expansion after the correction; destination internal draft; Gusto not prepared. | m8 | REAL · synthetic data |
| 1:40-1:51 | Under the hood: diagram | Three agent cards with tool lists; coordinator bar; Band arrows; Cognee store. | e1 | ILLUSTRATION · architecture |
| 1:51-2:03 | Under the hood: Band | Band Desktop: room with three agents + owner, board pending -> in progress -> completed, `[decision.requested]` and the owner's `approve <batch_id>` reply. | e2 | REAL · Band Desktop |
| 2:03-2:15 | Under the hood: metering + memory boundary | App activity log: tokens/cost per agent call (OpenRouter usage events); recall check showing approval_created false; memory off -> still asks. | e3 | REAL |
| 2:15-2:25 | Result | Stage 1 wages and each Stage 2 item separately with blockers; Export workbook toast (verified totals, original not updated); "Gusto: not prepared". | c1 | REAL workbook · synthetic data |
| 2:25-2:32 | Close | Mark + wordmark; "From missing information to payroll-ready. With you in control."; "You approve every message and correction. PayrollPilot never submits payroll."; one chip per integration from the evidence matrix; repo URL. | c2 | ILLUSTRATION |

Story share: hook, reveal, diagram and close = 43 s of 152 s (28%). Product and engineering footage = 72%. This follows the owner's cut, which replaced the earlier 40/60 target.

## Narration (cue time = start in the film)

- **h1** at 0:01.0: Running payroll shouldn't mean chasing down your entire team.
- **h2** at 0:06.4: Missing hours.
- **h3** at 0:08.6: Unassigned expenses.
- **h4** at 0:11.0: Numbers that don't add up.
- **r1** at 0:18.8: Meet PayrollPilot. Your AI-powered payroll operations team.
- **m1** at 0:25.6: This is a real pay period, on synthetic data, every record labeled. The audit agent finds an already-paid shift logged to the wrong job.
- **m2** at 0:35.6: It can't ask anyone, so it hands the case to Resolution, in a shared Band room.
- **m3** at 0:42.4: Resolution drafts two questions. The owner approves the exact text, and only then does it send: a real iMessage, in test mode, to the owner's own phone.
- **m4** at 0:54.6: A vague yes isn't an answer. Both questions are marked ambiguous, and one bounded follow-up goes out, with a new approval.
- **m5** at 1:03.4: The clear reply lands in the right case, quote attached, and the confirmed fact is stored in Cognee.
- **m6** at 1:10.6: The owner approves a local correction. Wages don't move; that shift was already paid. Job costing does, and only the affected item changes.
- **m7** at 1:21.6: In an earlier verified run, a fresh Payroll Prep process recalled the confirmed fact from Cognee and proposed an allocation for owner approval.
- **m8** at 1:32.4: Then Payroll Prep assembles the corrected review: an internal draft, waiting for the owner.
- **e1** at 1:40.8: Under the hood, three agents share one model, but not one set of powers. Plain code owns every state change and every approval.
- **e2** at 1:51.6: They coordinate in Band: one room, a shared board, every handoff acknowledged, and the owner's decision as a reply in that room.
- **e3** at 2:03.6: Each agent's model usage is metered. And memory can change a next action, but it can never grant an approval.
- **c1** at 2:15.4: Wages, commissions, tips and the manager pool stay separate, each with named blockers. The workbook is verified. And Gusto: not prepared.
- **c2** at 2:26.4: From missing information to payroll-ready. With you in control.

## Claim-to-evidence map (every narrated claim has a matrix row)

| Claim | Matrix row |
|---|---|
| Real pay period on synthetic data, every record labeled | R20, R21 |
| Audit finds an already-paid shift on the wrong job (seeded) | R11 |
| Audit cannot message; hands the case to Resolution in a Band room | R02, R03, R04 |
| Owner approves the exact text before any send | R06 |
| Real iMessage, test mode, only the owner's phone | R07, R08 |
| Vague yes -> ambiguous -> one bounded follow-up with new approval | R10 |
| Clear reply lands in the right case, quote attached | R09 |
| Confirmed fact stored in Cognee | R13 |
| Local correction approved; wages unchanged; job costing changes; only the affected item | R11, R12 |
| In a separate process, Payroll Prep recalls and proposes instead of asking | R14, R15 |
| Corrected internal review | R16 |
| One room, shared board, handoffs acknowledged, owner decision as a room reply | R03, R04, R05 |
| Each agent's model usage is metered | R19 |
| Memory changes a next action but never grants approval | R15 |
| Separate readiness with named blockers; workbook verified; Gusto not prepared | R16, R17, R18 |
| Owner approves everything; nothing submits payroll | R06, R12, R18 |

## Cuts if a proof is missing at 2:30 PM (never fake a beat)

- **No live iMessage**: 0:42-1:10 uses the bridge's dev adapter only if labeled "SIMULATED (dev adapter)" on screen, and m3-m5 narration drops "real iMessage"; the close chip reads NOT SHOWN. Better: a genuine earlier run labeled PLAYBACK.
- **No in-app Cognee clip**: 1:21-1:32 shows a terminal recording of the proven write -> separate fresh-process recall run (`python -m payrollpilot.memory.demo_recall`), labeled PLAYBACK · Cognee CLI · earlier verified run.
- **No Band Desktop footage**: 0:35-0:42 and 1:51-2:03 show a terminal recording of `python -m payrollpilot.band.demo_handoff` and `band room messages`, labeled REAL · Band CLI; never a mock of the Band app.
- **No usage footage**: e3 drops "Each agent's model usage is metered." and 2:03-2:15 shows only the recall boundary.
- **Owner's Band decision not captured**: e2 drops "and the owner's decision as a reply in that room."
