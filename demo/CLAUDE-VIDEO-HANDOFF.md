# Claude final-video handoff

**Ownership:** Claude owns final video script, disclosed generated narration, assembly and rendering. E has stopped duplicate narration/render edits and supports assets/evidence. **Record PayrollPilot demo footage** owns automatic captures on `cloud/film`, writing only `demo/film/clips/`. C owns the single phone-reply cue; the owner only replies and foregrounds Band. No live backend/bridge restart, reset or reenactment of already-applied effects.

## Assets and verified baseline

- Existing source: `demo/film/` (Remotion 4.0.537); frozen light identity in `design/DESIGN.md` FROZEN section, reference `design/home.html`. Reference is not product footage.
- Lead has the local **PayrollPilot-light-draft.mp4** output. It is a review draft with missing product slots: 152.000 seconds, 960×540 H.264/AAC, 4,560 frames, complete decode exit 0, audio mean −20.2 dB / peak −2.9 dB. Title/product/close and revised recall frames inspected. This is not upload-ready footage.
- Lead has the working nonsynced scratch runtime with dependencies and generated draft audio/music; obtain its local location privately. Avoid copying large node_modules into synced Documents, where file-provider activity stalled the earlier runtime.
- Preserve the exact close: **“From missing information to payroll-ready. With you in control.”** Claims stay within PRODUCT-STATEMENT.md “It can” and actually evidenced scope.

## Automatic capture → film mapping

| Source from capture chat | Intended use / limit |
|---|---|
| `01-home-in-progress.mp4` | Home overview / approval. Do not narrate issue detail that is not shown. |
| `02-approve-and-send.mp4` | Real exact-text approval/send on the C-agreed case. |
| `03-reply-ambiguous.mp4`, `04-clarify-approve.mp4` | Actual test-reply classification and approved clarification. |
| `05-answer-and-correction.mp4` | Actual reply/proposal only if captured. |
| `06-approve-apply-readiness.mp4` | Genuine fresh apply/readiness transition only if C’s safe case supports it. The earlier correction is already applied; never reenact it as new. |
| `07-ready-summary.mp4` | Real separate readiness and Gusto: not prepared; keep genuine blockers. |
| `08-band-room.png`, `09-band-board.png`, `12-band-chat-handoff.png` | Actual native room/plan/board/handoff/human-decision views. A single still does not prove a filmed transition; use genuine task history or real before/after captures and describe accurately. |
| `11-band-cost.png`, `11-band-usage.txt` | Native visibility, **with attribution unavailable if still true**. App metrics/unrelated sessions cannot substitute. |
| `13-band-dev-team.png` | Actual participating coding-team context only; not product-agent cost proof. |
| `10-cognee-recall.txt` | Sanitized real API evidence artifact; render as a clearly labeled log if appropriate, never a mock Cognee graph/app. Inspect actual result/error before narration. |

The current source still expects legacy `public/footage/*.mov`, three physical-phone files, and video-only slots. **No numbered-file importer or PNG/log support was implemented by E.** Adapt these explicitly. There is no physical-phone capture planned: use app-only reply layouts; do not put duplicated app footage into a fake phone frame. Captures remain pending until the capture chat reports paths/durations/provenance/privacy checks and the assembler inspects them.

## Required proof and honest gaps

[Mandatory checklist](mandatory-band-capture.md), [redacted native-view guide](evidence/band/mandatory-capture-references.md), [native usage support research / sponsor question](band-native-usage-research.md).

- Band: shared room with actual participating agents; lead plan; claimed/completed work on one board; routed @handoffs and ACKs; real human decision; native per-agent sessions/tokens/estimated cost view. Exact private internal references remain with C/the owner.
- Native product cost attribution is still **REQUIRED GAP** in the checked generic OpenRouter setup. Empty native sessions/unattributed totals are not zero/free model usage. SDK `Emit.USAGE` timeline events are not verified as the canonical native cost view.
- The owner’s actual new Claude video-assembly coding session may offer legitimate native usage **for video assembly** if Band attributes the real session. C/capture must verify its identity, actual PayrollPilot work and room/team association. Do not rename it as Audit/Resolution/Payroll Prep cost, invent a transcript/binding, or use unrelated agent history. No runtime binding/install was performed by E.
- Cognee: historical cross-process behavior proof exists; C-07 main notes also establish current-flow reply/write and observed ask→propose behavior change. Separate full-response/cross-process evidence is tracked in PR #38. Do not label the identical-baseline-query timeout/500 attempts successful. Runtime proof and pending video are different statuses.
- Confirmed selected-slice application/workbook does not mean all payroll ready. Preserve Stage 1/Stage 2 blockers, synthetic data, test reply and any playback labels; nothing submits payroll.

## Voice and working render commands

Generated narration is authorized for the final film; no owner imitation or owner-voice claim. Generate from the **final factual script**, verify each line/duration and complete audio, and disclose the generated voice. Current `say` files are still draft/placeholder. Current final preflight accepts only `owner`/`elevenlabs`; support an explicit verified generated-narration source truthfully, rather than flipping metadata to owner/ElevenLabs. E did not make that final-code/voice change after ownership transferred.

From `demo/film/`:

```bash
./node_modules/.bin/tsc -p .
node scripts/manifest.mjs
node scripts/preflight.mjs --final
./node_modules/.bin/remotion render PayrollPilotFilm out/payrollpilot-film.mp4 --codec h264 --crf 18 --concurrency 4 --browser-executable '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,nb_frames -of compact out/payrollpilot-film.mp4
ffmpeg -hide_banner -i out/payrollpilot-film.mp4 -af volumedetect -f null - > out/decode.log 2>&1
```

The installed Chrome override worked; bundled headless shell stalled. Measured draft used `--crf 28 --scale 0.5`; final command above is full source resolution and unbenchmarked. The current final gate intentionally rejects missing media/pending evidence/placeholder voice. Keep any unsatisfied mandatory criterion explicit; a technical export must not claim track compliance.

## Timing and minimum usable cutoff

- Feature freeze **2:45 PM Pacific**; capture chat’s committed clips deadline **3:00**; owner upload **by 3:15**; verify playback/access/receipt before **3:30**.
- Measured 152-second 540p draft took roughly 8–10 minutes under load; an 11-second revised section took roughly 2–3 minutes including setup. Full 1080p is unbenchmarked: conservatively budget 12–20 minutes, plus 2–5 for QA/encode; reserve 5–10 for upload because bandwidth is unknown.
- Safest full-render cutoff: critical media/script locked **2:40–2:45**, render start **2:45–2:50**. A complete high-quality rerender first started after all clips arrive at 3:00 is not a safe promise for upload by 3:15.
- Reuse verified unchanged story/title sections, ingest/render genuine product sections as they arrive, and trim optional illustration/polish. Do not fill missing proof with fiction to meet the clock. No E duplicate render or submission.

## Lead review of shared film branch, 2:33 PM Pacific

`cloud/film` now contains the real incremental capture files and generated Kokoro voice assets. Preserve both writers with ordinary merges; never force-push. The following narration corrections are required before a final cut:

- Segment 12 currently claims Band tracks every agent's sessions/tokens/cost. The actual native view is **unattributed** and no product-agent attribution has been verified. Say that the native view is shown but product-agent attribution remains unavailable. Do not label machine-wide totals as product-agent spend.
- Segment 13 claims the coding team coordinated in Band. Use that claim only if capture 13 actually proves the participating Claude Code/Codex sessions and their collaboration. Codex chat coordination alone does not establish it.
- Segments 08–09's known wages-zero / $200 allocation belongs to the **earlier owner-applied correction**, not the newly sent nine-question batch. If showing its real applied details, explicitly narrate it as earlier verified work; do not imply a fresh Approve & Apply click or replay a completed action. The new missing-job case has an unconfirmed rate, so its monetary impact is unknown.
- Segment 11 must describe the **selected case** reaching Done; other genuine cases remain open. Never imply every case or all payroll is complete.
- Segment 04 must match the captured approval channel. The earlier human Band decision is real historical evidence; the new send used the reviewed web action. Distinguish the two visibly.
- Ambiguous/clear reply segments require the actual new inbound events and captures. At this checkpoint the ambiguity clip is still waiting for the owner's reply; cut or mark unavailable if it does not occur.
- Current generated Kokoro narration must be disclosed and verified against the corrected factual script; existing script comments still call it placeholder. A metadata change alone is not a factual correction.

These are claim/evidence corrections, not changes to payroll rules, permissions or readiness.
