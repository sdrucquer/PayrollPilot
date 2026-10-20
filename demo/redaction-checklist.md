# Redaction checklist (run before every take and before committing any evidence)

Tick every line. One failure means the frame or file does not ship.

## On screen and in files

- [ ] **Recipient masked everywhere**: UI shows `***-**NN` style only; phone thread header shows the contact name "PayrollPilot", not a number; notification banners off or name-only.
- [ ] **No real names**: workers are Worker A-D, the respondent is "Ops lead", the company is "Pilot Co". Check the Band room participant list and the phone contact names too.
- [ ] **No real rates or amounts beyond fixture placeholders** (2200/2500/3000 cents per hour; the $1,000 synthetic commission case). If the private snapshot is loaded, rates and amounts must render masked or the beat uses the fixture.
- [ ] **No private allocation percentages** (manager pool split). The manager pool card should show "blocked" with a code, not percentages.
- [ ] **No env or secrets**: no `.env`, no terminal scrollback with keys, no `export` lines, no OpenRouter/Photon/Browser Use dashboards. Terminal for the restart beat is a fresh window with `clear` run first.
- [ ] **Photon dashboard never on screen.** Same for Gusto, Jobber, QuickBooks pages that show company identity.
- [ ] **Band room minimized**: only the "PayrollPilot Cases" room visible; sidebar with other chats collapsed or cropped; case cards show id, category, title only.
- [ ] **Browser chrome clean**: no bookmarks bar, no other tabs with identifying titles, no extensions with account names, profile avatar hidden.
- [ ] **macOS**: menu-bar clock fine; hide Wi-Fi name? (not identifying, fine); hide the user account name in any title bars; close Messages on the Mac (it mirrors the thread with the number).
- [ ] **Files in `demo/evidence/`** (committed): PNG/JSON only after checking each for numbers, names, ids that map to real people, provider space ids. Raw captures stay in `demo/evidence/private/` (gitignored).
- [ ] **Labels visible**: provenance chips on every product card; health strip shows integration modes; test-mode banner visible during the messaging beats.

## Film-specific

- [ ] Every Remotion illustrative scene carries the ILLUSTRATION chip.
- [ ] Every product clip carries its provenance chip (REAL / SYNTHETIC / SEEDED ISSUE / TEST REPLY / PLAYBACK).
- [ ] The status card values match `demo/evidence-matrix.md` at render time.
- [ ] Final export scrubbed frame-by-frame at 2x through the phone and Band beats.

## Who checks

Lane E checks committed evidence files. The owner checks each take on playback. Lane F's privacy sweep (F-04, 2:35 PM) runs over the repo.
