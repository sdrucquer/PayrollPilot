> Current direction: FROZEN light identity in design/DESIGN.md and design/home.html. Product shots must come from the running app, Band, and Cognee views. No mockup or old fixture screenshot may stand in for a recording. All 14 unique clips remain pending. Owner records 2:45–3:15 Pacific. Label earlier takes PLAYBACK, data SYNTHETIC, owner answers TEST REPLY; REAL describes a verified integration.

# Shot list (v4, 2026-10-20 1:17 PM)

The app uses the frozen centered column: hero, approval, progress and activity; detailed evidence stays behind Details. Story and product sections share the light identity. Only the running app provides app proof.

**Record proof beats in live API mode only** (`cd web && npm run dev:api`, backend on :8000, bridge on :3001). The app's fixture mode has a "Simulate test reply" button and marks those messages "fixture simulation: not sent through Photon". That path is fine for rehearsing clicks but must never be cut into m3-m5 as the live iMessage beat. If it is ever used in the film, its chip must read SIMULATED.

No interim screenshot or design mockup substitutes for product footage; missing clips stay FOOTAGE PENDING.

Two kinds of material:
- **Motion graphics** (ILLUSTRATION), rendered by `demo/film/`: hook B-roll with fictional data, reveal, architecture diagram, close.
- **Product footage**, recorded by the owner (steps in `recording-setup.md`), cut into the clip names below with `demo/film/scripts/cut.sh`, dropped in `demo/film/public/footage/` (gitignored).

Capture: QuickTime "Record Selected Portion" of the browser window at 1440x900 (or as near 16:10 as the display allows), 30 fps, zoom 110%, bookmarks bar hidden. Phone: QuickTime "New Movie Recording" with the iPhone as camera over USB, Do Not Disturb on, only the PayrollPilot thread open.

| Clip | Film time | Source | Must be on screen | Chip | Proof owner |
|---|---|---|---|---|---|
| `m1-detect.mov` | 0:25-0:35 (10 s) | App | Frozen home with separate readiness, then open Details for the seeded issue "Already-paid shift on 2026-10-01 is on Job 01 but scheduled on Job 02"; Details shows observed vs expected, evidence, wages none / job costing | SEEDED ISSUE · synthetic data | B, D |
| `m2-band-handoff.mov` | 0:35-0:42 (7 s) | Band Desktop | PayrollPilot room (default title): pp-audit case card, pp-resolution acceptance, board task to in progress | REAL · Band Desktop | C |
| `m3-approve.mov` | 0:42-0:54 (12 s) | App | Drafted batch (two questions), masked recipient, linked issue ids, hash; Approve and send; batch state sent + provider status | REAL | C, D |
| `m3-phone.mov` | 0:48-0:54 (6 s) | Phone | Message arrives; thread header shows contact "PayrollPilot", no number | REAL · Photon iMessage · test mode | Owner |
| `m4-clarify.mov` | 0:54-1:03 (9 s) | App | Inbound "yes" labeled test reply; both questions ambiguous; Clarify; follow-up approval; sent | TEST REPLY | C, D |
| `m4-phone.mov` | 0:54-1:03 | Phone | Owner sends "yes"; follow-up arrives | TEST REPLY | Owner |
| `m5-answer.mov` | 1:03-1:10 (7 s) | App | Both answered: te_0014 -> job_02, Job 03 off-site for job_02; quote shown | TEST REPLY | C, D |
| `m5-phone.mov` | 1:03-1:10 | Phone | Owner sends the clear answer | TEST REPLY | Owner |
| `m6-correction.mov` | 1:10-1:21 (11 s) | App | Correction before/after; impact wages $0.00, labor moves Job 01 -> Job 02; Approve correction; Apply; only the affected Stage 2 item changes; row moves to resolved | REAL calc · synthetic data | A, B, D |
| `m7-cognee.mov` | 1:21-1:32 (11 s) | Separate recall view + app | Earlier cross-process proof labeled PLAYBACK, or a fresh recall process; leave backend :8000 and bridge :3001 running; later Job 03 disposal cost; activity log `memory.recalled` -> `memory.applied`; next action before/after strings | REAL · Cognee | C |
| `m8-review.mov` | 1:32-1:40 (8 s) | App | Stage 1 expansion after the correction (per-worker table, dashes for unknown); destination internal draft; Gusto not prepared | REAL · synthetic data | B, D |
| `e2-band.mov` | 1:51-2:03 (12 s) | Band Desktop | Room members (three agents + owner); board task pending -> in progress -> completed; `[decision.requested]` and the owner's `approve <batch_id>` reply | REAL · Band Desktop | C, owner |
| `e3-usage-recall.mov` | 2:03-2:15 (12 s) | App or terminal | Activity log with tokens/cost per agent call (OpenRouter usage events); recall check with approval_created false; memory-off control still asks | REAL | C, D |
| `c1-readiness.mov` | 2:15-2:25 (10 s) | App | Stage 1 wages and each Stage 2 item with its first blocker; Export workbook toast (draft version, verified totals, original not updated); "Gusto: not prepared" | REAL workbook · synthetic data | B, D |

Fallback clips (labeled, never presented as the app): terminal recording of `python -m payrollpilot.memory.demo_recall` (PLAYBACK · Cognee CLI · earlier verified run) for `m7-cognee.mov`; terminal recording of `python -m payrollpilot.band.demo_handoff` + `band room messages` (REAL · Band CLI) for `m2`/`e2`.

## Playback rule

If a live beat fails in the final take, use the same beat from the 2:20 PM rehearsal only if it was a genuine run, with its chip set to `PLAYBACK · genuine run at HH:MM`. Never re-enact a failed integration with a fake adapter and call it live.

## Never on screen

Photon dashboard; any `.env`; terminal history with keys; real names; phone numbers (thread header, contact card, banners); real rates; private allocation percentages; Jobber/Gusto/QuickBooks pages with company identity; unrelated Band chats. See `redaction-checklist.md`.
