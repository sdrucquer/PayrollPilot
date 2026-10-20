# Lane E: Demo, video, submission

Owner: Claude chat/session "E" (can be a Claude Code session in the repo; it only edits `demo/` and `README.md`). Branch `lane/e-demo`, worktree `../PayrollPilot-e`. Binding: shared context, `DEMO-PLAN.md` (lead's baseline; you extend it), AGENTS.
Owns: `demo/` (`script.md`, `shot-list.md`, `evidence-matrix.md`, `reply-script.md`, `redaction-checklist.md`, `submission.md`, `evidence/` index; `demo/evidence/private/` gitignored for raw captures), `README.md`, `docs/PRODUCT-BRIEF.md` (sanitized public brief). Must not edit code, contracts, or other plans.
Mission: a coherent 2-3 minute video and complete submission, prepared while features are built, with every integration claim backed by captured evidence and every synthetic/test element labeled. The owner records screen and phone and submits; you prepare everything so that takes under 30 minutes.

## Tasks

### E-01 Script v1 + shot list + evidence matrix (P0) — 30 min — start now
- Deps: none. Source: `DEMO-PLAN.md`, PRD 15.1 narrative, shared context clock.
- Write `demo/script.md`: timed narration (0:00-2:45) following the 7 beats: cycle + separate stage states; audit issue -> Band handoff; approve question -> real iMessage on phone; reply -> parse -> clarify/propose; approval -> recalculation, only affected readiness changes (T02 wages unchanged); restarted agent recalls Cognee memory and changes action; packet + workbook + Stage 2 item blockers + "Gusto: not prepared". Write `demo/shot-list.md`: per beat, the screen (route), the phone shot, Band views needed (room, board, human decision, usage), what is real/cached/synthetic/test reply/prerecorded. Write `demo/evidence-matrix.md`: rows = PRD FR-29/FR-30/FR-31 + sponsor brief items (Band: 2+ participants, shared board, dependent handoff, human decision, per-agent tokens/cost; Cognee: write, recall by other/restarted agent, behavior change; live text round trip; workbook; honest destination), columns = evidence artifact path, status (captured/pending/unavailable), who captures.
- Acceptance (FR-30, FR-31): every claim in the script maps to a matrix row; no row says captured without a file path.
- Verify: `ls demo/` and a read-through by the lead.

### E-02 Reply script, redaction checklist, recording setup (P0) — 20 min
- `demo/reply-script.md`: exact test replies the owner will send from the phone, in order, including one deliberately vague "yes" (shows clarification) and the final clear answer; timing cues. `demo/redaction-checklist.md`: mask recipient everywhere, no real names (Worker A, Ops lead), no rates beyond fixture placeholders, no env/dashboard views with ids/secrets, Band room content minimized, Photon dashboard never on screen. Recording setup: QuickTime screen recording at 1280x800 or the app window, phone screen via QuickTime (USB) or a second camera, mic check, Do Not Disturb, browser zoom 110%, close other apps. Rehearsal checklist with a 60-second dry run before G1.
- Acceptance: owner can follow it without asking questions.

### E-03 Evidence capture as it happens (P0, continuous) — from 1:00 PM
- When lanes report a proof (C-01 round trip, C-02 Band room/board/ask/usage, C-03 recall log, B-04 workbook screenshot, A-03 real read coverage), save the artifact under `demo/evidence/` (sanitized) or `demo/evidence/private/` (raw), update the matrix row to captured with the path. Ask lanes directly for screenshots via their PR comments or the owner.
- Acceptance: by 2:20 PM every required row is captured or marked unavailable with the honest reason.

### E-04 README, product brief, submission copy (P0) — 25 min, by 2:30 PM
- `README.md`: what it is, what is real vs synthetic in the demo, architecture summary (link ARCHITECTURE.md), run instructions (`scripts/dev.sh`, env names from `.env.example`), integration status table copied from INTEGRATION-FINDINGS, safety boundaries, team. `docs/PRODUCT-BRIEF.md`: sanitized one-page version of the PRD (no named allocations, rates, phone numbers). `demo/submission.md`: project description (150-300 words), tagline, team, repo URL, video URL placeholder, sponsor usage statements (Band, Cognee) worded exactly to what was proven, required fields checklist from the organizer brief (the PRD's S2; confirm fields with the owner), upload buffer plan (upload by 3:15 PM, verify playback + repo visibility + receipt by 3:25 PM).
- Acceptance: no unproven claim; every integration statement has a matrix row.

### E-05 Final recording support (P0) — 2:45-3:15 PM
- Sit with the owner through the recording: run the script, mark takes, note which beats are live vs playback of the earlier successful run (label playback on screen or in narration), export, check audio, hand the file to the owner for upload. Record what was actually done in `demo/evidence-matrix.md`.

## Status log
