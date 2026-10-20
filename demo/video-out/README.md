# PayrollPilot demo video

File: `payrollpilot-demo.mp4`. 1920x1080, 30 fps, H.264 + AAC, about 2:35.
Play: any player (`open payrollpilot-demo.mp4`, VLC, QuickTime, browser).
Source: Remotion project in `demo/film/` (`src/v2/`). Rebuild: see "Render" below.

## Voice

Narration is **AI-generated with Kokoro** (open-source TTS, Apache-2.0, voice `af_heart`), run locally from `demo/film/narration.txt`. It is not the owner's voice. No ElevenLabs key was available in the render environment. Owner recordings dropped into `demo/film/public/vo/owner/<id>.m4a` replace lines one by one on the next render. Captions are burned in.

Sound effects and music are **synthesized in code** by `demo/film/scripts/sound.py` (numpy; no samples, no licensed tracks):
- 83 cues are computed from the film timeline (`demo/film/public/sound/cues.json`): dings for message bubbles, pops for Band messages, an impact on the logo reveal, a glitch on the process exit, and varied transitions at scene cuts.
- The music is an original pad-and-pulse bed at 100 BPM. It ducks under the voice with a sidechain compressor and is loudness-normalized to about −14 LUFS (peak −0.7 dB).
- The video stream is copied untouched.
- `payrollpilot-demo-voice-only.mp4` is the same cut with narration only.

Mix command, from `demo/video-out/`:

```bash
python ../film/scripts/sound.py ../film/public/sound
ffmpeg -i voice-only.mp4 -i ../film/public/sound/sfx.wav -i ../film/public/sound/music.wav -filter_complex "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[vo][vosc];[2:a]volume=0.32[m];[m][vosc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=450[md];[1:a]volume=0.42[s];[vo][s][md]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.93[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k mixed.mp4
ffmpeg -i mixed.mp4 -map 0 -c:v copy -af loudnorm=I=-14:TP=-1.0:LRA=11 -c:a aac -b:a 192k payrollpilot-demo.mp4
```

## What is real, per segment

Every segment carries an on-screen label. Data is synthetic (Pilot Co, Worker A–D, Ops lead).

| Time | Segment | Source | Label |
|---|---|---|---|
| 0:00–0:13 | Hook: flood of timesheets, texts, receipts | Motion graphics, fictional data | Illustration |
| 0:13–0:21 | Logo reveal | Owner's logo | Illustration |
| 0:21–0:29 | Gather from Jobber, QuickBooks, Gusto | Motion graphic of the gather step on the synthetic cycle | Synthetic data |
| 0:29–0:39 | Audit finds issues and routes them to who knows | Motion graphic; seeded issues from the synthetic cycle | Synthetic data |
| 0:39–0:57 | Home with one approval; approve and send | **Real app recordings** `01-home-in-progress.mp4`, `02-approve-and-send.mp4` (Playwright, local running app) | Real |
| 0:39–1:38 (right panel) | Band room messages | **Exact text** from the native Band room capture (`12-band-chat-handoff.png`, 1:16–2:07 PM), re-typeset; owner's name replaced with "Owner" | Real (exact messages) |
| 0:57–1:05 | iMessage sent; activity rows | Activity rows from today's event log (approval 1:32:23 PM, Photon send 1:32:24 PM, provider id prefix `spc-msg-b022a2ba`, test reply 1:32:55 PM) | Real · Test reply |
| 0:57–1:19 (phone) | iMessage thread | **Rebuilt** from the owner's phone screenshot with the exact message text; one personal name masked | Illustration · Test reply |
| 1:05–1:38 (app window) | App while the reply is handled | **Real app recording** `07-ready-summary.mp4` (actual state after the send: "Pilot is working on it", waiting on the Ops lead) | Real |
| 1:18–1:28 | Correction card: $200 Job 01 → Job 02, wages $0.00 | Values from the earlier verified correction `corr_a647520203` (applied earlier today, on an earlier case than the batch sent in clip 02) | Recorded earlier today · Synthetic data |
| 1:28–1:36 | Readiness card after apply | Illustrated card over the real app; Band `[correction.applied]` and pp-payroll ACK messages are real (2:07 PM) | Illustration |
| 1:38–1:47 | Band product room | **Native Band Desktop screenshot**, name and username covered, menu bar and dock cropped | Real |
| 1:47–1:53 | Band work board | **Native Band screenshot** (state at 2:31 PM: 2 Done, 11 In progress); still image, not filmed motion | Real |
| 1:53–1:57 | Band usage and estimated cost | **Native Band screenshot**; usage is build-team sessions, **unattributed**, not product-agent cost | Real |
| 1:57–2:14 | Cognee memory | Terminal: earlier cross-process proof (write, exit, fresh process recall; 1:00 PM run). Result card: real `POST /api/memory/recall-check` (`10-cognee-recall.txt`): `applied: true`, ask → propose job_02, `approval_created: false` | Recorded earlier today · Real |
| 2:14–2:25 | Recap | First: **real app recording** `07-ready-summary.mp4` (actual blocked state: wages 1 of 4, answers needed, Gusto not prepared). Then the ready state from `design/ready.html` | Real, then Design mockup |
| 2:25–2:35 | Close | Logo and text | — |

Not shown because no genuine capture exists: a real ambiguous-reply app clip, a fresh Approve & Apply click, and a Claude Code + Codex build team in Band (the segment is removed automatically when `13-band-dev-team.png` is absent).

## Render

From `demo/film/`:

```bash
npm ci
python scripts/tts_kokoro.py <kokoro.onnx> <voices.bin> af_heart   # regenerate voice
node scripts/assets.mjs                                             # collect clips, time segments
npx remotion bundle src/index.ts --out-dir /tmp/pp-bundle
npx remotion render /tmp/pp-bundle PayrollPilotDemo ../video-out/payrollpilot-demo.mp4 --codec h264 --crf 20 --concurrency 4 --browser-executable <chrome-headless-shell>
```
