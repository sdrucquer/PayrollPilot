# PayrollPilot launch film + demo: timed script (v1, 2026-10-20 12:50 PM)

Owner direction (12:40 PM): a launch-film look (Apple/Linear), roughly 40% story and 60% genuine product and technical demonstration, under three minutes, every illustrative sequence visibly distinct from verified functionality. This script extends the lead's baseline in `DEMO-PLAN.md` (same seven product beats, same order, same labels). Differences from the baseline: a launch-film opening and close are added per the owner's direction, and narration is a generated voiceover instead of the owner speaking (owner can still record their own voice over the same timings).

Runtime target **2:55** (hard cap 3:00). Narration ~395 words at ~156 wpm (2.6 words/s), timed per line below. Voiceover: ElevenLabs if the owner supplies a key before 2:15 PM, otherwise a labeled placeholder voice (see `demo/film/README.md`). Every on-screen clip carries one of the labels **REAL**, **CACHED**, **SYNTHETIC**, **SEEDED ISSUE**, **TEST REPLY**, **PLAYBACK** (genuine earlier run), or **ILLUSTRATION** (motion graphics, not the product).

Label rule: illustrative sequences use the film's dark gradient and a persistent small "ILLUSTRATION" chip bottom-left. Product sequences are full-frame screen footage with a provenance chip bottom-left taken from the UI's own `provenance` field plus the integration mode from `/api/health` (for example "REAL · Photon iMessage", "REAL · Band Desktop", "REAL · Cognee", "SYNTHETIC fixture"). Nothing in the product section is mocked up in the film; if a feature is not proven by 2:30 PM its beat is cut or shown as a blocked card, never animated to look working.

| Time | Section | Visual (see shot-list.md) | VO line | Label |
|---|---|---|---|---|
| 0:00-0:03 | Cold open | Black. Cursor blink, one soft tick. "Friday, 4:52 PM." types on. | 01 | ILLUSTRATION |
| 0:03-0:15 | Problem montage | Kinetic type, one fragment per cut (~0.7s): "4 timesheets", "3 systems", "1 spreadsheet", "a shift with no job", "a receipt nobody can place", "who quoted job 2?", "pay it anyway?". Fragments stack and jitter; low drone builds. | 02 | ILLUSTRATION |
| 0:15-0:24 | Turn | Fragments collapse into one thin horizontal rule; drone resolves to a clean tone. | 03 | ILLUSTRATION |
| 0:24-0:32 | Logo reveal | Rule becomes the wordmark baseline; mark draws on; "PayrollPilot" resolves with tight tracking; tagline "Payroll, prepared. Never guessed." First full chord. | 04 (at 0:28) | ILLUSTRATION |
| 0:32-0:50 | How it works | Three cards (Audit, Resolution, Payroll Prep) with their tool lists; a solid bar under them, "Deterministic coordinator: state, permissions, approvals"; handoff arrows; an owner-decision marker at each effect; "Band Desktop" and "Cognee" tags on the arrows and the memory store. | 05 | ILLUSTRATION |
| 0:50-0:51 | Transition | Coordinator bar morphs into the real app header; product footage fades up beneath. | - | - |
| 0:51-1:05 | Beat 1: Cycle board | REAL UI, zone 1 progress strip + zone 2: Pilot Co, period, coverage chips, Stage 1 card, three separate Stage 2 cards with readiness and blocker codes, destination badge. | 06 | SYNTHETIC fixture (or REAL · Browser Use read if A-03 landed) |
| 1:05-1:23 | Beat 2: Audit -> Band handoff | REAL UI zone 2 row -> zone 3 panel, seeded issue "Already-paid shift on 2026-10-01 is on Job 01 but scheduled on Job 02" (stage impact: wages none, job costing); click Hand off. Band Desktop: room "PayrollPilot Cases" with pp-audit, pp-resolution, pp-payroll; case card; board item moves; `band ask` decision answered by the owner. | 07 | REAL · Band Desktop · SEEDED ISSUE |
| 1:23-1:40 | Beat 3: Approve -> real iMessage | REAL UI: drafted batch of two questions (the Oct 1 shift's job; which job the Job 03 off-site disposal run belongs to); approval dialog with exact text, masked recipient, linked issue ids, hash; Approve + Send. Phone: message arrives. | 08 | REAL · Photon iMessage |
| 1:40-1:55 | Beat 4: Reply -> parse -> clarify | Phone: vague "yes". UI: TEST REPLY inbound, both questions "ambiguous", Clarify; re-approve, send. Phone: clear answer. UI: "answered", extracted job, quote. | 09 | REAL transport · TEST REPLY |
| 1:55-2:09 | Beat 5: Correction -> recalc | UI: correction before/after; impact "Stage 1 wages delta $0.00", labor moves from Job 01 to Job 02; approve (second approval); apply; only the affected card changes; `readiness.changed` for that item. | 10 | REAL calc · SYNTHETIC data |
| 2:09-2:26 | Beat 6: Restart -> Cognee recall | Terminal: backend stop and start, timestamps visible. UI activity log under the strip: `memory.recalled`, `memory.applied` by Payroll Prep for a later disposal cost on Job 03; next action before ("ask ops lead which job") vs after ("propose allocation to Job 02, needs owner approval"); hit text with evidence refs. Exact strings come from lane C's run. | 11 | REAL · Cognee |
| 2:26-2:40 | Beat 7: Packet, workbook, honest destination | UI Stage 1 expansion (packet table); Export workbook toast -> sheets, verified totals, `original_updated: false`; Stage 2 cards: quote commission ready (synthetic case $1,000 -> $50 -> $25/$25), tips pending, manager pool blocked `policy_missing:*`; "Gusto: not prepared". 2s cut of the xlsx with pending tabs. | 12 | REAL workbook · SYNTHETIC data |
| 2:40-2:48 | Status card | "What you just saw": one row per integration with its actual label, from the evidence matrix; Band usage tokens/cost per agent if captured. | 13 | ILLUSTRATION card, values from evidence |
| 2:48-2:55 | Close | Wordmark, repo URL, "Built in one day at the AI Startup Challenge, SF". Music resolves. | 14 | ILLUSTRATION |

Story share: 0:00-0:51 and 2:40-2:55 = 66s of 175s (38%). Product share 62%.

## Narration text (clean, for ElevenLabs or the placeholder voice)

Numbered lines match `demo/film/public/vo/NN.mp3`. Seconds are at 2.6 words/s.

01. (1s) Friday, 4:52 PM.
02. (10s) Every two weeks, a home-service business owner reconciles hours, jobs, receipts and commissions by hand. Across three tools that don't talk. And one spreadsheet that remembers nothing.
03. (8s) What if payroll came to you already checked, with the questions already asked, and nothing paid until you said so?
04. (2s) PayrollPilot. Payroll, prepared. Never guessed.
05. (17s) Three agents share one model, not one set of powers. Audit finds issues. Resolution asks people. Payroll Prep assembles the result. Plain code owns every approval, so no agent, message or memory can grant itself permission. They hand off in Band Desktop, and remember with Cognee.
06. (13s) A real pay period, loaded from a synthetic snapshot, every record labeled. Wages are Stage 1. Commissions, tips and the manager pool are Stage 2, each with its own state. Nothing rolls up to complete.
07. (18s) The audit agent found an already-paid shift logged to the wrong job. It can't ask anyone, so it hands the case to Resolution in a Band Desktop room shared by all three agents and the owner. The board moves. The human decision is a real Band prompt.
08. (16s) Resolution drafts two questions for the ops lead. The owner approves the exact text and recipient; change a character and the approval dies. In test mode, only the owner's phone is allowed. And here it is: a real iMessage, through Photon.
09. (14s) A vague yes to two questions isn't an answer. Both are marked ambiguous, and a bounded clarification goes out: same person, same issues, new approval. The clear reply lands in the right case, quote attached.
10. (13s) The confirmed fact becomes a local correction, never a source write, approved separately. Wages don't move; that shift was already paid. Job costing does, and only the readiness that depends on it changes.
11. (15s) Now the process restarts. A different agent, Payroll Prep, meets a disposal receipt on that same off-site job. It recalls the earlier resolution from Cognee, checks the references still exist, and proposes instead of re-asking. Memory never creates an approval.
12. (12s) A review packet and a twelve-ledger workbook, verified against each other. Missing policy shows as a blocker, with its code. And the destination is honest: Gusto, not prepared. Nothing was submitted.
13. (6s) Everything you saw was labeled: what was live, what was synthetic, what was a test reply.
14. (1s) PayrollPilot. Payroll, prepared.

Line 06 says "synthetic snapshot". If A-03 lands a real read and the owner records against it, change to "loaded from a real, read-only Jobber snapshot" and relabel Beat 1.

## Claim-to-evidence map (every narrated claim has a matrix row)

| Claim in narration | Evidence matrix row |
|---|---|
| Separate Stage 1 / Stage 2 states, no roll-up | R01 |
| Audit cannot message; Resolution can (tool allowlists) | R02 |
| Already-paid shift on the wrong job detected with evidence (seeded issue) | R11 |
| Band room with three agents, board move, human decision | R03, R04, R05 |
| Approval bound to exact text and recipient; change invalidates | R06 |
| Only the owner's phone is an allowed recipient | R07 |
| Real iMessage delivered via Photon | R08 |
| Real reply correlated to the case | R09 |
| Vague reply -> ambiguous -> bounded clarification | R10 |
| Local correction, wages unchanged, job costing changed, affected readiness only | R11 |
| Source record never written | R12 |
| Restart; other agent recalls Cognee; next action changes; no approval created | R13, R14, R15 |
| Packet and workbook verified against each other; 12 ledgers; `original_updated: false` | R16 |
| Stage 2 item blockers with codes; policy missing shown honestly | R17 |
| Destination "Gusto: not prepared"; nothing submitted | R18 |
| Per-agent tokens/cost in Band usage | R19 |
| Every element labeled real/cached/synthetic/seeded/test | R20 |

## Cuts if behind (in order)

1. Beat 4 clarification half (keep the clear reply only): saves 8s.
2. "How it works" diagram shortened to 10s: saves 7s.
3. Beat 7 xlsx quick cut: saves 4s.
4. If Band product proof is not captured by 2:30 PM: Beat 2 becomes the UI handoff event only, narration changes to "hands the case to Resolution" with no Band claim, and the status card says "Band Desktop: not shown".
5. If Cognee recall is not captured: Beat 6 is cut; status card says "Cognee: write proven / recall not shown" or "not shown".
6. If the iMessage round trip is not captured: the film is not submitted as a launch film with that claim; Beat 3-4 use the labeled fallback (Telegram) or are replaced by the FakeMessaging dev flow labeled "SIMULATED (dev adapter)".
