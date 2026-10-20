# PayrollPilot launch film (Remotion)

A 2:32 draft with reserved slots for real running-app, Band, and Cognee footage. Current recordings: none. Product slots stay FOOTAGE PENDING; this draft reviews timing and the frozen light identity. Script and timings: `demo/script.md`. Shot list and clip names: `demo/shot-list.md`.

## Honesty rules built into the film

- Every illustrated scene carries an **ILLUSTRATION** chip.
- Static mockups and fixture screenshots cannot substitute for product recordings. The owner supplies captures; Lane E does not record the screen. Earlier recordings must say PLAYBACK, with SYNTHETIC data and TEST REPLY labels retained.
- Every product segment carries the label from `src/beats.ts`. While its footage file is missing it renders a dashed "FOOTAGE PENDING" frame and a grey **PLANNED** chip; nothing is mocked to look like the app.
- The closing card reads `src/status.json`. Lane E sets each row only from `demo/evidence-matrix.md`. A final render must have `"draft": false` and no `pending` rows.
- A top-right watermark appears whenever the render is a draft, the voice is the placeholder, or clips are missing.

## Commands (from `demo/film/`)

```bash
npm ci
```

```bash
node scripts/vo.mjs
```
Voiceover: uses ElevenLabs if `ELEVENLABS_API_KEY` is set in the environment or in `demo/film/.env` (gitignored; optional `ELEVENLABS_VOICE_ID`), else the macOS `say` placeholder voice. Regenerate one line with `node scripts/vo.mjs 07`.

```bash
node scripts/music.mjs
```
Synthesized original music and transition sounds (no samples, no licensing).

```bash
scripts/cut.sh public/footage/take1-screen.mov 00:12.0 00:26.5 s1-board.mov
```
Cuts a named clip from a raw take (names in `demo/shot-list.md`). `public/footage/` is gitignored.

```bash
node scripts/manifest.mjs
```
Rebuilds `src/generated/manifest.json` (clip and voice durations) and checks that no voice line overlaps the next. Run before every render.

```bash
npx remotion render PayrollPilotFilm out/payrollpilot-film.mp4 --codec h264 --crf 18
```
Full 1080p render, about 4-6 minutes on the M3. `npx remotion studio` previews live.

## Final export check

```bash
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact out/payrollpilot-film.mp4
```
Expect h264 1920x1080, aac, duration under 180 s. Then watch it end to end with sound and run `demo/redaction-checklist.md`.

## Before the owner records and exports

Use the actual running app in live API mode, plus the real Band room/board and Cognee recall view. `design/home.html` is an identity reference only. Keep app/data labels visible; an earlier take is PLAYBACK, synthetic records are SYNTHETIC, and the owner's reply is TEST REPLY. Verify each REAL label against the evidence matrix, never against a mock or a narrated intention.

Run `node scripts/preflight.mjs` for the draft report. Run `node scripts/preflight.mjs --final` before the final render; it exits 1 while footage, evidence statuses or final voice are missing. It does not replace the owner's complete playback and redaction check. The current draft is not upload-ready.

The validated local renderer uses `--browser-executable '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'` on this machine. Earlier cross-process Cognee proof is PLAYBACK; leave the live backend and bridge running.
