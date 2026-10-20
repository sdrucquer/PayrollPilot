# Lane E validation — October 20, 2026

Only demo/, README.md and docs/PRODUCT-BRIEF.md authored in this pass. Main merges import upstream application changes; no application, contract, financial-policy or plan edits by Lane E. Public team identity Shanin Drucquer is owner-authorized and separate from private pilot data.

## Commands actually run and results

- `git fetch origin`: succeeded; main advanced during the pass from 3e8f641 to 62f9b98, bcb5251 and 00b110a. Guidance read on origin/main, including the lane Status log; frozen design and home.html used as references, never product footage.
- `git checkout -b lane/e-demo-e02 origin/lane/e-demo-e02`; `git checkout -b lane/e-demo-e06 origin/lane/e-demo-e06`; `git checkout -b lane/e-demo-e04 origin/lane/e-demo-e04`: tracking branches created.
- `git merge origin/main` / `git merge --stat origin/main` on all three: automatic ort merges. `git merge lane/e-demo-e02` into e06 conflicted in evidence matrix/script/shot list; retained modern e06 structure and both non-overlapping fixes (room reply, safe separate-process proof). `git merge lane/e-demo-e06` into e04 conflicted in README/submission; retained final 215-word E-04 structure plus latest integration evidence and recording fixes.
- `python3 /tmp/fix_lane_e_recording.py`, `python3 /tmp/refresh_lane_e_content.py`, `python3 /tmp/update_lane_e_integrations.py`: applied lane-only recording, styling/evidence and overlapping-copy updates.
- `./demo/film/node_modules/.bin/tsc -p demo/film`: exit 0, no errors.
- `node demo/film/scripts/vo.mjs m7`: exit 0 in temporary runtime; local say placeholder regenerated to describe the earlier verified fresh-process recall. No provider call.
- `node demo/film/scripts/manifest.mjs`: exit 0; all 18 VO lines fit, minimum slack 0.9s; new m7 8.0s, 2.8s slack; 0 product clips; say voice; music/bed.wav.
- `node demo/film/scripts/preflight.mjs --final`: exit 1 as intended: 14/14 clips missing, draft closing card, pending evidence, say voice. No final-media completion claim.
- `git diff --check`: final exit 0. Earlier whitespace error corrected.
- Python checks of README/submission/brief: local links all resolve; 215-word description within 150–300; stale backend-stop, working-band-ask, dark-stage and interim-still instructions absent. No application tests run; integration notes copied from main, not rerun.
- `git push origin lane/e-demo-e02 lane/e-demo-e06` and `git push origin lane/e-demo-e04`: successful normal pushes, no force/history rewrite.

## Render and media results

From demo/film:

```bash
./node_modules/.bin/remotion render PayrollPilotFilm out/payrollpilot-film-light-draft.mp4 --codec h264 --crf 28 --scale 0.5 --concurrency 4 --browser-executable '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' > out/light-render.log 2>&1
./node_modules/.bin/remotion render PayrollPilotFilm out/light-recall-update.mp4 --frames 2430-2759 --codec h264 --crf 28 --scale 0.5 --concurrency 4 --browser-executable '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' > out/recall-render.log 2>&1
```

Both succeeded. The original full light render is `out/light-base.mp4` in the final temporary runtime. The revised Cognee section is 330 frames. All other film source/VO is unchanged from the full render. Reassembled exactly at frames 2430–2759:

```bash
ffmpeg -y -loglevel error -i out/light-base.mp4 -i out/light-recall-update.mp4 -filter_complex '[0:v]trim=start_frame=0:end_frame=2430,setpts=N/(30*TB)[v0];[0:a]atrim=start=0:end=81,asetpts=PTS-STARTPTS[a0];[1:v]setpts=N/(30*TB)[v1];[1:a]atrim=duration=11,asetpts=PTS-STARTPTS[a1];[0:v]trim=start_frame=2760:end_frame=4560,setpts=N/(30*TB)[v2];[0:a]atrim=start=92:end=152,asetpts=PTS-STARTPTS[a2];[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]' -map '[v]' -map '[a]' -r 30 -c:v libx264 -preset veryfast -crf 28 -c:a aac -movflags +faststart out/payrollpilot-film-light-draft.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,nb_frames -of compact out/payrollpilot-film-light-draft.mp4
ffmpeg -hide_banner -i out/payrollpilot-film-light-draft.mp4 -af volumedetect -f null - > out/decode.log 2>&1
ffmpeg -y -loglevel error -ss 85 -i out/payrollpilot-film-light-draft.mp4 -frames:v 1 out/recall-qa.png
```

Actual results: h264 960x540, 4560 video frames, AAC, 152.000 seconds. Complete decode exit 0; mean audio -20.2 dB, maximum -2.9 dB. Inspected title/product/close frames and revised recall frame: light identity, legible planned/playback labels, close intact. No complete human playback/listening or final redaction sign-off claimed.

## Environment failures and recovery

Bundled Chromium failed under the sandbox (bind/MachPort); permissioned bundled shell stalled, then own renderer terminated. Installed Chrome override succeeded. Some cleanup/render commands first used the wrong working directory and failed; corrected and rerun. The synced Documents scratch checkout later stalled in file-provider activity; transient audio probes there failed. Its later scratch-only commits (including generated assets immediately untracked) were never pushed. Preserved that checkout; recreated changes from the existing remote heads in /private/tmp/payrollpilot-lane-e-runtime, normal forward commits only. Stopped only this lane's stalled scratch git/render processes; no live payroll services touched. Original local dependencies/audio reused; corrected VO and manifest succeed in temporary runtime.

No screen recording, payroll action, Band/email message, upload, submission or PR merge. Owner supplies real app/Band/Cognee clips, labels earlier takes PLAYBACK and answers TEST REPLY, reviews audio/redaction and submits. Final current-flow Cognee comparison remains pending; earlier independent-process proof is not upgraded to a completed current live loop.
