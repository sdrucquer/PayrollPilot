# Submission (draft, 1:02 PM; final by 2:30 PM, values refreshed at 3:05 PM after the render)

Fields follow `DEMO-PLAN.md` "Submission fields". Confirm the organizer's exact field list with the owner; anything marked [OWNER] needs the owner.

## Project name
PayrollPilot

## Tagline (one line)
Payroll, prepared. Never guessed.

## One-line description
AI agents that audit a small business's pay period, ask the right person by text, and prepare payroll the owner can trust, without ever submitting it.

## Description (~230 words)

Small home-service businesses run payroll from tools that disagree: time and jobs in one app, payroll in another, costs in the books and the bank. Every two weeks the owner reconciles them by hand, and the usual fixes are guesses.

PayrollPilot prepares the payroll instead of guessing it. It loads one pay period, runs deterministic audits, and raises exceptions with evidence: a paid shift on the wrong job, an open timer, a receipt nobody can place. Three agents share one model but not one set of powers. Audit finds issues and cannot message anyone. Resolution drafts one question for the right person, and it is sent only after the owner approves the exact text; change a character and the approval is void. Replies are parsed per question, a vague "yes" triggers a bounded clarification, and confirmed facts become local corrections the owner approves. Payroll Prep shows readiness separately for wages and for each commission, tip, and manager-pool item, with blocker codes instead of defaults, and exports a verified reconciliation workbook.

A plain-code coordinator owns every state change and permission. Agents hand cases to each other in a Band Desktop room, and confirmed facts are stored in Cognee so a restarted agent recalls them and proposes the known answer instead of asking again. Nothing writes to source systems and nothing submits payroll: the destination reads "Gusto: not prepared".

## Sponsor usage (main 27b40ae evidence; final footage pending)

- **Band:** Audit, Resolution and Payroll Prep share a room and board; existing CLI proof shows the dependent handoff. Main reports the owner's `approve <batch_id>` room reply produced version-bound approval at 1:32. `band ask` is unsupported; no per-product-agent Band usage claim. Desktop footage pending.
- **Cognee:** A fact was written and recalled by a fresh process using CHUNKS search; validated recall changed the proposal without granting approval. Main also reports a live memory write at 1:33. No graph-completion claim. Use earlier proof as PLAYBACK; no live stack restart.
- **Photon:** Main reports a real allowlisted send/reply at 1:12–1:14 and a 1:32 owner-approved batch with correlated TEST REPLY and live parsing. Phone/app clips remain pending; fixture simulation does not prove iMessage.

[Sanitized evidence](evidence/logs/live-flow-main27b.txt), [matrix](evidence-matrix.md). Real Jobber read is partial: 58 entries, 10 workers, 13 jobs; totals, ids, source approval unverified, rates/payroll/payments/expenses not read. The film uses synthetic data. Final voice and all 14 product clips remain pending.

## Links
- Repo: https://github.com/sdrucquer/PayrollPilot (public; verify before submitting)
- Video: [OWNER pastes URL after upload]
- Team: [OWNER]

## Required fields checklist
- [ ] Project name
- [ ] Tagline / one-liner
- [ ] Description (150-300 words)
- [ ] Repo URL, public, README renders
- [ ] Video URL, plays in a private window, under 3:00, sound works
- [ ] Team members [OWNER]
- [ ] Sponsor integrations used, each statement matches `demo/evidence-matrix.md`
- [ ] Any extra organizer fields [OWNER confirms from the organizer brief]

## Upload buffer plan
| Time | Step | Who |
|---|---|---|
| 2:20 | Rehearsal recording, every beat live; becomes PLAYBACK backup | Owner |
| 2:30 | This file, README, product brief final (except video URL) | Lane E |
| 2:45-2:55 | Final take (screen + phone) | Owner |
| 2:55-3:05 | Lane E cuts clips, sets status card from the matrix, renders 1080p (~5 min) | Lane E |
| 3:05 | Owner watches the export end to end with sound; redaction check | Owner |
| 3:10-3:15 | Upload begins (fallback: upload the rehearsal-based render if the final render fails) | Owner |
| 3:15-3:25 | Verify playback in a private window, repo public, paste URLs, submit, screenshot receipt | Owner |
| 3:30 | Deadline | |
