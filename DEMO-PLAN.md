# Demo plan (lead baseline; lane E extends in `demo/`)

Target: one coherent 2:30-2:50 video. Screen recording of the web app (1280 wide) with a phone inset for the iMessage beats and two short Band Desktop views. Narration by the owner. Everything labeled.

## Timed script (v0)

| Time | Beat | Screen | Proves | Label on screen |
|---|---|---|---|---|
| 0:00-0:15 | Problem + promise: "payroll looks complete while records are not; PayrollPilot prepares and explains, the owner approves." | Cycle board | Separate Stage 1 / Stage 2 states, coverage chips, destination `not prepared` | provenance badge: `synthetic` or `real (Browser Use read, <date>)` |
| 0:15-0:35 | Audit finds an issue: a paid shift logged against the wrong job (allocation-only) and one unassigned entry. | Inbox -> thread (evidence refs, stage impact: wages none / job costing) | FR-04/05/08 | `seeded issue` if seeded |
| 0:35-0:50 | Audit hands the case to Resolution through Band. | Band room: `pp-audit` card -> `pp-resolution` ack; board item moves | Band: 2+ agents, dependent handoff, board | real |
| 0:50-1:15 | Owner reviews the grouped question (exact text, masked recipient, linked issues) and approves. Phone buzzes. | Approval dialog -> phone inset showing the iMessage | Live text, approval binding, allowlist | `test mode: sent to owner's phone; intended respondent: Ops lead` |
| 1:15-1:40 | Owner replies vaguely ("yes"); agent marks ambiguous and asks one bounded clarification; owner answers clearly. | Thread: parsed statuses, clarification batch, second approval | FR-11/12, T14 | `test reply` |
| 1:40-2:00 | Correction proposed (before/after, impact: wages $0 change, job cost moves); owner approves via Band ask or UI; readiness updates only for the affected item. | Review/approval -> board | FR-13/14, T02, Band human decision | real |
| 2:00-2:20 | A restarted Payroll Preparation agent evaluates a later disposal receipt on the off-site job: Cognee recall of the confirmed job relationship changes its next action from "ask" to "propose allocation (needs approval)". | Activity feed: `memory.recalled`, `memory.applied` with before/after; terminal or UI showing restart | Cognee write + recall by restarted agent + behavior change | real |
| 2:20-2:40 | Review packet + workbook: Stage 1 review-ready for N of M workers, Stage 2: "1 commission ready (synthetic case: $1,000 -> $50 -> $25/$25); tips pending; manager pool blocked (overhead policy O05)"; workbook generated with 12 ledgers, pending tabs present, `original not updated`; destination `Gusto: not prepared`. Band usage view flash (tokens/cost per agent). | Review page + xlsx opened + Band usage | FR-16/19/21/22/28, honest labels | `internal draft` |
| 2:40-2:50 | Close: what is real today, what is gated (source writes, Gusto draft), link to repo. | Board | FR-31 | |

## Evidence matrix (lane E keeps the live version in `demo/evidence-matrix.md`)

| Requirement | Evidence to capture | Source lane | Status |
|---|---|---|---|
| Live text round trip (FR-10/11) | Phone screenshot (masked), `message.sent` event with provider id, inbound event | C, owner | pending |
| Band: participants, board, handoff, human decision, usage (FR-29) | Band room screenshot, board screenshot, `ask` answer screenshot, `band usage` output | C | pending |
| Cognee write + recall changes action (FR-15/29, T15) | recall-check JSON before/after; restart log | C | pending |
| Allocation-only correction leaves wages unchanged (T02) | Review screen before/after | A, B, D | pending |
| Workbook with 12 ledgers, verified totals, original not updated (FR-28) | xlsx screenshot, `WorkbookArtifact` JSON | B, A | pending |
| Honest labels (FR-31) | Board with provenance + destination badges | D | pending |
| Real data read (optional) | coverage block from snapshot (no private rows) | A | pending / fallback |

## What is real vs not (declare in narration)
- Real: iMessage send/receive, Band room/board/decision/usage, Cognee write/recall, approvals, calculations, workbook file.
- Synthetic or seeded: the pay-period data unless A-03 succeeds (then "real read, de-identified display"); the quote-commission case ($1,000 profit) is a labeled synthetic fixture.
- Playback: if a live beat fails during the final take, use the G2 rehearsal recording of that beat and say "recorded earlier today".
- Unavailable: Gusto draft, source writes, real manager pool totals (shown as blocked).

## Human tasks (owner)
1. Add phone to Photon account now; keep the phone unlocked and on the desk for the recording.
2. Reply from the phone exactly per `demo/reply-script.md`.
3. Answer the Band `ask` prompt when it appears (one click).
4. Record screen (QuickTime, 1280x800 window) and phone (QuickTime via USB or second camera) from 2:45; one full take, one backup take.
5. Export, play back start to end, upload by 3:15, verify the upload plays and the repo is public; keep the receipt.

## Recording setup checklist
Do Not Disturb on both devices; browser at 110%; `.env`, dashboards, and terminal with keys never on screen; Band room content minimized (case ids and categories only); test mode banner visible; mic test 10 s; rehearsal at 2:20 captured as backup.

## Submission fields (fill from organizer brief; confirm with owner)
Project name, one-line description, 150-300 word description, repo URL (public), video URL, team, sponsor integrations used (Band, Cognee) with one sentence each stating exactly what was proven, optional deck (skip).
