# Implementation roadmap (2026-10-20, America/Los_Angeles)

Planning started 12:11 PM. Lanes A, B, C launched 12:31 PM; D, E launched 12:34 PM. Deadline 3:30 PM. Feature freeze 2:45 PM. Upload by 3:15 PM. Build time available at launch: about 2 h 10 min before freeze.

## Dependency graph

```
B-01 fixtures ──┬──> A-02 load/audit routes ──> D-02 inbox/thread ──> G1 flow
                ├──> B-02 audit rules ─────────┘        ^
                ├──> B-03 calc + readiness ──> B-05 corrections ──> A-04 apply/readiness/packet/workbook ──> D-03 review/workbook
                ├──> B-04 workbook ───────────────────────────────────┘
                ├──> D-01 board (fixture mode)            ├──> F-02 safety suite
                └──> F-01 contract tests                  └──> F-03 rehearsal (G1, G2)
A-01 scaffold/persistence/permissions ──> A-02 ──> C-05 comms routes ──> G1
C-01 Photon round trip (independent spike) ──> C-05
C-03 Cognee proof (independent spike) ──> G2 memory beat
C-02 Band product handoff (independent spike) ──> G2 handoff beat
C-04 agents on OpenRouter ──> C-05
A-03 Browser Use real read (independent, timeboxed) ──> real-data label in demo (else fixture)
E-01/E-02 (independent) ──> E-03 evidence capture (continuous) ──> E-04 README/submission ──> E-05 recording support
```

## Critical path
A-01 -> A-02 -> C-05 -> (D-02) -> G1 live round trip -> A-04 -> G2 (Band + Cognee beats proven) -> freeze -> recording -> upload. Everything else runs beside it. The lead merges in this order: B-01, A-01, D-01, B-02/B-03, A-02, C-01 bridge, C-05, B-04/B-05, A-04, D-02/D-03, C-02/C-03/C-04 proofs, F tests, E docs.

## Time budget

| Window | Lead (integrator) | Expect from lanes |
|---|---|---|
| 12:50-1:15 | Merge B-01, A-01, D-01; answer ownership questions; owner setup (Photon phone, env keys) | A-01 done; B-01 fixtures up; C-01 echo or Telegram fallback decision; D-01 board on fixtures; E-01 draft |
| 1:15 **G0** | Verify: backend health, audit returns expected exceptions, board renders via API | |
| 1:15-1:50 | Merge A-02, B-02, B-03, C-01, C-05; run F-01 | C-03 recall proof; C-02 Band commands verified; D-02; B-05; E-02 |
| 1:50 **G1** | Lead + F run the live round trip with the owner's phone; capture evidence (E) | |
| 1:50-2:20 | Merge A-04, B-04, D-03, C-02, C-04; F-02 results | Band handoff visible; Cognee recall changes action; workbook export; A-03 real read result or fallback decision |
| 2:20 **G2** | Full rehearsal recording (keep as labeled backup) | E-04 README/submission draft |
| 2:20-2:45 | Fix-only merges; F-04 privacy sweep at 2:35 | D-04 polish only if green |
| 2:45 **freeze** | Tag `v0.1-hackathon`; final recording with owner | E-05 |
| 3:15 | Upload begins; verify playback, repo public access, receipt | |

## Cut order (apply at the first missed gate)
1. A-03 live Browser Use read (use owner export or fixture, labeled).
2. Real manager-pool figures (keep blocked card with blocker codes).
3. Clarification loop automation (keep ambiguous detection + manual clarify button).
4. Cognee graph completion (keep CHUNKS recall; still real Cognee).
5. UI polish (D-04), activity filters.
6. Band `ask` human decision via Band (keep UI approval + Band room messages) only if `ask` cannot be made to work; document.
Never cut: real message round trip, approval gates, exception evidence, workbook export, one Band handoff, one Cognee recall, recording time.

## Owner setup needed (in priority order)
1. Photon: add a phone to the account (dashboard said `account_phone_missing`); give lane C the project credentials via `bridge/.env` only.
2. `backend/.env`: `OPENROUTER_API_KEY` and `LLM_API_KEY` (same value), `PP_TEST_RECIPIENT`; `bridge/.env`: `PP_TEST_RECIPIENT`, `PP_BRIDGE_TOKEN` (same in both).
3. Confirm pilot cycle dates against Gusto (O01) and put `BROWSER_USE_API_KEY` in `backend/.env` if A-03 is to run; log into Jobber in the Browser Use profile when lane A asks.
4. Restart any Claude Code session that should appear in Band (plugin installed 12:45 PM).
5. Rotate the OpenRouter key after the event (it was pasted in chat).
