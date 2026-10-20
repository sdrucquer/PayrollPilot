# Integrated rehearsal (F-03)

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
