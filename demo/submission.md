# PayrollPilot submission copy and owner upload runbook

Date: October 20, 2026. All times Pacific. Copy is ready; the video URL is filled after the owner uploads. This document does not certify missing video evidence or submit an entry.

## Paste-ready fields

**Project:** PayrollPilot

**Team:** Shanin Drucquer

**Tagline:** From missing information to payroll-ready. With you in control.

**One line:** Payroll preparation that turns evidence-backed exceptions into owner-approved corrections and separate readiness for wages and compensation items.

**Repository:** https://github.com/sdrucquer/PayrollPilot

**Video:** OWNER: paste the uploaded, playable video URL here.

**Description (150–300 words):**

Payroll preparation can stall on a missing job assignment, an unclear shift, or a cost that does not match its records. PayrollPilot helps one home-service business turn those questions into a review the owner can assess.

It detects missing, unassigned, long, overlapping, or duplicate time and mismatched or duplicated costs, with source evidence and stage impact. It groups questions by respondent for a real iMessage through Photon after the owner approves the exact text and recipient. In test mode, messages go only to the owner's allowlisted phone. It parses replies, flags vague, partial, or conflicting answers, and asks a bounded follow-up within the same scope.

PayrollPilot proposes local corrections with before-and-after values and calculation impact. Only owner-approved corrections are applied, followed by recalculation of wages and job costs. Employee wages and each Stage 2 item—quote commission, tips, and manager pool—retain independent readiness and named blockers. A 12-ledger review workbook includes pending tabs and totals checked against the on-screen draft.

Cases can pass between agents through Band with a human decision, while confirmed facts recalled from Cognee can change a later action. The demo uses labeled synthetic records and test replies; the evidence notes below distinguish tested integrations from pending captures. PayrollPilot does not submit payroll or write to source systems. The owner stays in control.

## Sponsor evidence notes (use only the supported scope)

- **Band:** Three product agents participated in a real Band room; the existing CLI proof reports a dependent Audit → Resolution → Payroll Prep handoff and board movement. Owner decision and Desktop footage remain pending. Do not claim a completed human decision, working `band ask`, or per-product-agent Band usage. Evidence: [R03–R05 / R19](evidence-matrix.md), [handoff log](evidence/band/handoff-run.txt).
- **Cognee:** Existing cross-process proof reports a stored fact recalled by a fresh process using local CHUNKS search. The validated recall changed the proposed next action without creating approval. In-app footage remains pending. Do not claim LLM-backed graph extraction or graph-completion search. Evidence: [R13–R15](evidence-matrix.md), [recall log](evidence/cognee/recall-run.txt).
- **Photon:** No verified round-trip claim in the submission evidence snapshot. Add a demonstrated-use statement only after the owner captures both approved outbound and correlated inbound events with the phone result, R08–R09. Fixture reply simulation is not a real iMessage.

The description follows `docs/PRODUCT-STATEMENT.md` “It can”; it describes capability, not a completed live demonstration. Never paste stronger integration claims than the evidence supports. No real source-read claim.

## Owner’s final steps

| Time | Action | Completion evidence |
|---|---|---|
| Before 2:45 | Confirm the organizer form’s fields; preserve this copy. Check the running app’s health/adapters and synthetic/test labels. | Form inspected by owner; no credentials on screen. |
| 2:45 | Feature freeze. Begin recording real app, Band and Cognee views using [shot list](shot-list.md) and [reply script](reply-script.md). | Owner raw take; Lane E does not screen-record. |
| 2:45–2:55 | One complete take plus short pickups. Keep owner approvals, synthetic data and test replies visible. | Real footage for each selected beat; prior take labeled PLAYBACK. |
| 2:55–3:05 | Cut named clips, rebuild manifest, update evidence and closing status from what is actually shown, render. | Run film commands below; preserve pending/unavailable distinctions. |
| 3:05–3:10 | Watch the whole export with sound and complete [redaction checklist](redaction-checklist.md). | No pending frames, missing sound, private details or unproven claims. |
| **By 3:15** | Owner uploads the verified video; paste its URL above and into the form. | Upload completed / playable link. Begin earlier if upload time is uncertain. |
| 3:15–3:25 | Open video and repo signed out; verify sound, full duration and access. Owner submits and saves receipt. | Playback verified, public repo accessible, submission receipt saved privately. |
| **3:30** | Deadline. | Owner verifies receipt before this time. |

If a live beat fails, use an earlier successful owner recording labeled PLAYBACK. If there is no successful recording, cut that claim and mark it unavailable; never replace it with a mock or a simulation labeled real. The present draft has no product clips and is not an upload fallback.

From `demo/film/`:

```bash
node scripts/manifest.mjs
node scripts/preflight.mjs --final
npx remotion render PayrollPilotFilm out/payrollpilot-film.mp4 --codec h264 --crf 18
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact out/payrollpilot-film.mp4
```

The final gate currently refuses missing clips, pending closing statuses and placeholder voice. Use owner narration or configured final voice, update `public/vo/source.txt` truthfully, and rebuild the manifest. If a beat is cut, update the timeline, narration, shot list and final evidence scope together. For the uncut film expect 152 seconds; export must stay under three minutes. A successful technical gate still needs the owner’s full playback/redaction review.

## Form checklist (owner completes at upload)

- [x] Project, tagline, one line, description, team and repository copy prepared.
- [ ] Organizer field list / eligibility / any required declarations checked in the actual form.
- [ ] Final video contains real running-product footage, accurate labels and verified claims.
- [ ] Band and Cognee statements match the evidence actually shown.
- [ ] Video URL pasted; signed-out playback and audio verified.
- [ ] Repository visibility / access verified signed out.
- [ ] Owner submitted; receipt saved privately.
