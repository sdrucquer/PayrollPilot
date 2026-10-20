# PayrollPilot launch film (Remotion)

A 2:55 film: ~38% illustrated launch story (cold open, problem montage, logo, architecture), ~62% real product footage, closing status card. Script and timings: `demo/script.md`. Shot list and clip names: `demo/shot-list.md`.

## Honesty rules built into the film

- Every illustrated scene carries an **ILLUSTRATION** chip.
- Every product segment carries the label from `src/beats.ts`. While its footage file is missing it renders a dashed "FOOTAGE PENDING" frame and a grey **PLANNED** chip; nothing is mocked to look like the app.
- The closing card reads `src/status.json`. Lane E sets each row only from `demo/evidence-matrix.md`. A final render must have `"draft": false` and no `pending` rows.
- A top-right watermark appears whenever the render is a draft, the voice is the placeholder, or clips are missing.

## Commands (from `demo/film/`)

```bash
npm install
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
