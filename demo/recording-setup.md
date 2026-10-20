# Recording setup and rehearsal checklist (owner)

Goal: capture clean product clips that drop into the launch film, in under 30 minutes, with one backup take. Lane E prepares; the owner records and submits.

## Machine setup (5 min, do it at 2:15 PM and again at 2:40 PM)

1. Close everything except: browser (one window, one tab on `http://localhost:5173`), Band Desktop (room "PayrollPilot Cases"), one clean Terminal window for a separate recall process, QuickTime.
2. Quit Messages on the Mac (it mirrors the phone thread and can show the number). Quit Slack, mail, calendars.
3. Do Not Disturb on the Mac (Control Center -> Focus -> Do Not Disturb).
4. Browser: dark mode, zoom 110%, bookmarks bar hidden (Cmd-Shift-B), window sized to 1440x900 (or as large as the display allows at 16:10).
5. Check `/api/health` in the UI's header strip shows the intended modes (Messaging: Photon; Memory: Cognee; Band: enabled). If any says fake/null, that beat is labeled or cut, not recorded as live.
6. Run `demo/redaction-checklist.md`.

## Phone setup (3 min)

1. Do Not Disturb with Messages allowed, or Focus off and all other notifications silenced.
2. Brightness high, auto-lock Never during the take.
3. Contact "PayrollPilot" saved for the sender; thread open.
4. Replies copied into Notes (from `demo/reply-script.md`).
5. Capture: plug into the Mac by USB, QuickTime -> File -> New Movie Recording -> camera dropdown -> the iPhone. Second option: another phone filming the screen on a stand. Third option: iOS Screen Recording from Control Center (no mic), AirDrop the file after.

## Capture (QuickTime)

- Screen: File -> New Screen Recording -> Record Selected Portion around the browser window; Options -> microphone None (voiceover is added in the film) unless you are narrating live.
- Record one continuous take of beats 1-7 with the phone recording running at the same time. Clap once on camera at the start (sync point for the two recordings).
- Save as `demo/film/public/footage/take1-screen.mov` and `take1-phone.mov` (gitignored folder). Lane E cuts them into the named clips in `shot-list.md`.
- Band beats: either switch to Band Desktop inside the same screen recording (Cmd-Tab), or record Band separately as `s2b-band-room.mov`.
- Cognee beat: use existing cross-process proof, labeled PLAYBACK with the original time, or have lane C provide a separate fresh recall process. Do not stop or restart backend :8000 or bridge :3001. No data reset or memory deletion during recording.

## Rehearsal checklist (60-second dry run before G1, full run at 2:20 PM)

- [ ] 60 s dry run (before 1:50 PM): open board, open the seeded issue, click Draft, open approval dialog, cancel. Confirms the route and buttons exist. No send.
- [ ] 2:20 PM full rehearsal: every beat in order with real sends, recorded. This is the PLAYBACK backup for the final.
- [ ] After the rehearsal: lane E reviews the clip, notes timings and failures, updates `script.md` cuts.
- [ ] Coordinate the final synthetic case with lane C. Do not reload the cycle, clear Cognee, or reset the running stack; lane C controls safe case preparation.
- [ ] Final take at 2:45 PM. Backup take immediately after if time allows.
- [ ] Hand both files to lane E (drop in the footage folder); lane E renders the film by about 3:05 PM.

## After the render (owner)

1. Watch the exported `demo/film/out/payrollpilot-film.mp4` end to end with sound. Check the redaction list at 2x on phone and Band beats.
2. Upload (YouTube unlisted or the organizer's uploader) by 3:15 PM. Paste the URL into `demo/submission.md` and the submission form.
3. Open the uploaded video in a private window: it plays, sound works, length under 3:00.
4. Confirm the repo `sdrucquer/PayrollPilot` is public and README renders. Submit. Screenshot the receipt.
