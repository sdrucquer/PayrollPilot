# Integrated rehearsal (F-03)

For the existing owner-gated live stack, use `scripts/f_smoke.sh --observe --out tests/integration/REHEARSAL.md`.
This performs GET-only checks and inspects existing event evidence. It never reloads the cycle, creates
approvals, sends, applies corrections, generates a workbook, invokes recall, or restarts a service.
Missing required evidence is a failure; skipped effects are not new live proofs. The exact T15
before/after response and `approval_created=false` must be captured by Lane C separately.
The default and `--send` modes below are **mutating isolated rehearsals**, despite the old “dry run” name;
do not run them on the active owner-gated loop or follow their fresh-database/restart guidance there.

Script: `scripts/f_smoke.sh` (dry run) or `scripts/f_smoke.sh --send --out tests/integration/REHEARSAL.md` (real send + wait for the owner's real reply).

How to run a rehearsal:
- Use a **fresh backend database** for each rehearsal (for example `PP_DB_PATH=/tmp/pp-rehearsal.db`). A second run against the same database re-proposes an already applied correction, so the T02 delta shows as empty.
- `--send` texts the allowlisted handle once (the backend and the bridge both enforce the allowlist). The owner replies from the phone within `REPLY_WAIT` seconds (default 240). Nothing in the script fakes a reply.
- The exit code is the number of FAILed steps.

## Pre-rehearsal check, 2026-10-20 13:15 PDT (isolated, not the live demo database)

Run against a separate backend on a temporary database so the shared demo state was not touched. Bridge (:3001) and web (:5173) were the live services (read-only health checks).

| Backend code | Messaging | Steps | Result |
|---|---|---|---|
| main @ 69c672e | none (no comms routes) | 20 | 16 pass, 4 FAIL: handoff, draft, approve send, recall-check all 404 because C-05 is not on main |
| lane/c-04 merged with main | fake (labeled synthetic) | 21 | 19 pass, 2 FAIL: handoff 503 band_required (Band disabled in the isolated instance), no real reply (`REPLY_WAIT=0`) |

Observed in the second run:
- draft, approve, send all 200; retry send returned `duplicate: true` with one provider send and one `message.sent` event.
- T02 correction: wages delta 0, job labor -20000 / +20000; apply 200; Stage 1 readiness unchanged.
- After apply, Job 01's commission still has 11 blockers and `readiness_changes` is empty: this is the known A-04 bug (the fixed exception stays `detected`), tracked by the strict xfail in backend/tests/test_f_safety.py.
- packet `internal_draft`; workbook verified, 13 sheets, same draft version as the packet.
- recall-check 200 with 0 hits (no resolution was written in this run, so nothing to recall).

Blockers for a real G2 rehearsal on the live stack:
1. C-05 must be on main (PR #17 merged into lane/c-04, not main).
2. Lane A apply bug (fixed exception stays detected) for the "readiness changes" beat.

## Pre-rehearsal check on main, 2026-10-20 13:18 PDT (isolated, fake messaging)

main @ 38ccd0d now has the C-05 routes (lane C #28) and the A-04 exception-resolution fix (#27).

| Backend code | Messaging | Steps | Result |
|---|---|---|---|
| main @ 38ccd0d | fake (labeled synthetic) | 21 | 19 pass, 2 FAIL: handoff 503 band_required (Band disabled in the isolated instance), no real reply (`REPLY_WAIT=0`) |

- draft 200 to the masked test handle; approve 200; send 200 (synthetic); retry returned `duplicate: true`.
- T02 correction: wages delta 0; job labor -20000 / +20000; apply 200 with `readiness_changes` = ci_quote_job_01, ci_manager_pool; Stage 1 unchanged; Job 01 commission blockers 11 -> 10. The readiness beat works.
- packet internal_draft; workbook verified, 13 sheets, same draft version.

Earlier blockers 1 and 2 are cleared. For the live G2 rehearsal: start the backend with a fresh `PP_DB_PATH`, `PP_BAND_ENABLED=1` and `PP_MESSAGING=bridge`, then run `scripts/f_smoke.sh --send --out tests/integration/REHEARSAL.md` while the owner has the test phone ready to reply.

## Rehearsal 2026-10-20 14:20 PDT (send=0, observe=1)

**Current operating instruction:** the fresh-backend / `--send` directions above are historical and superseded for the active recording stack. Keep the existing backend and bridge running; use only `--observe` here. Default/`--send` mutates cases and must not be used on the owner's active loop.

GET-only observation of existing evidence; no new send, reply, approval, correction, workbook or recall was performed. Missing required evidence fails; skipped actions are not proofs.

| # | step | result | http | detail |
|---|---|---|---|---|
| 1 | backend health | PASS | 200 | existing process; no restart |
| 2 | active real comms | PASS | 200 | requires bridge, Cognee, Band CLI and configured model/room |
| 3 | bridge health | PASS | 200 | requires real bridge |
| 4 | web served | PASS | 200 | HTTP availability only; API-mode UI must be checked separately |
| 5 | existing cycle | PASS | 200 | existing cycle; not reloaded or audited |
| 6 | exception evidence | PASS | 200 | evidence present; no private record text printed |
| 7 | readiness available | PASS | 200 | readiness reported; blocked items remain blocked |
| 8 | review packet | PASS | 200 | internal draft only; nothing submitted |
| 9 | event trail | PASS | 200 | current cycle audit trail |
| 10 | Band handoff evidence | PASS | 200 | recorded handoff.accepted count=2; no new action performed |
| 11 | recorded live round trip | PASS | 200 | requires correlated bridge send, inbound and parsed reply |
| 12 | owner approval log | PASS | 200 | recorded approval.granted count=3; no new action performed |
| 13 | correction applied | PASS | 200 | recorded correction.applied count=1; no new action performed |
| 14 | readiness change log | PASS | 200 | recorded readiness.changed count=2; no new action performed |
| 15 | Cognee write log | PASS | 200 | recorded memory.written count=2; no new action performed |
| 16 | Cognee recall log | PASS | 200 | requires recorded Cognee adapter; HTTP 200 alone is insufficient |
| 17 | memory action change log | PASS | 200 | requires recorded proposal to job_02 with resolution refs; full before/after proof belongs in C ledger |
| 18 | workbook verification log | PASS | 200 | requires matching generated/verified artifact; no workbook generated now |
| 19 | new effects | SKIP | - | owner alone approves; send/apply/export/recall not invoked |
| 20 | exact T15 comparison | SKIP | - | use C's captured response before/after and approval_created=false; event counts alone do not establish every T15 condition |

Result: 0 FAIL of 20 steps.
