# Voiceover: two ways to record

Both paths produce one file per line in `demo/film/public/vo/<id>.mp3`. The film places each file at its cue time, so lines can be re-recorded one at a time.

## Path A: ElevenLabs (preferred if a key is available)

1. Put the key in `demo/film/.env` (gitignored): `ELEVENLABS_API_KEY=...`. Optional: `ELEVENLABS_VOICE_ID=...` to pick a voice (default is a calm male narrator voice).
2. From `demo/film/`:

```bash
node scripts/vo.mjs
```

```bash
node scripts/manifest.mjs
```
The second command prints each line's length and flags any overlap with the next cue. If a line overlaps, shorten the text in `src/narration.json` and in `demo/script.md`, then re-run the first command with just that line id.

## Path B: the owner's own voice

1. Quiet room, phone or laptop mic 20 cm away, Voice Memos or QuickTime audio.
2. Read each line below as its own take, with a one-second pause before and after. Pace: calm and unhurried, about the speed you'd explain this to an investor.
3. Export each take as `<id>.m4a` into `demo/film/public/vo/`, then from `demo/film/`:

```bash
for f in public/vo/*.m4a; do ffmpeg -y -loglevel error -i "$f" -af "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,loudnorm=I=-16:TP=-1.5" -ar 44100 -ac 2 "${f%.m4a}.mp3"; done; echo owner > public/vo/source.txt
```

```bash
node scripts/manifest.mjs
```

| Id | Cue | Line |
|---|---|---|
| h1 | 0:01.0 | Running payroll shouldn't mean chasing down your entire team. |
| h2 | 0:06.4 | Missing hours. |
| h3 | 0:08.6 | Unassigned expenses. |
| h4 | 0:11.0 | Numbers that don't add up. |
| r1 | 0:18.8 | Meet PayrollPilot. Your AI-powered payroll operations team. |
| m1 | 0:25.6 | This is a real pay period, on synthetic data, every record labeled. The audit agent finds an already-paid shift logged to the wrong job. |
| m2 | 0:35.6 | It can't ask anyone, so it hands the case to Resolution, in a shared Band room. |
| m3 | 0:42.4 | Resolution drafts two questions. The owner approves the exact text, and only then does it send: a real iMessage, in test mode, to the owner's own phone. |
| m4 | 0:54.6 | A vague yes isn't an answer. Both questions are marked ambiguous, and one bounded follow-up goes out, with a new approval. |
| m5 | 1:03.4 | The clear reply lands in the right case, quote attached, and the confirmed fact is stored in Cognee. |
| m6 | 1:10.6 | The owner approves a local correction. Wages don't move; that shift was already paid. Job costing does, and only the affected item changes. |
| m7 | 1:21.6 | Later, a disposal cost arrives for the same off-site job. After a restart, Payroll Prep recalls the answer from Cognee, and proposes instead of asking again. |
| m8 | 1:32.4 | Then Payroll Prep assembles the corrected review: an internal draft, waiting for the owner. |
| e1 | 1:40.8 | Under the hood, three agents share one model, but not one set of powers. Plain code owns every state change and every approval. |
| e2 | 1:51.6 | They coordinate in Band: one room, a shared board, every handoff acknowledged, and the owner's decision as a reply in that room. |
| e3 | 2:03.6 | Each agent's model usage is metered. And memory can change a next action, but it can never grant an approval. |
| c1 | 2:15.4 | Wages, commissions, tips and the manager pool stay separate, each with named blockers. The workbook is verified. And Gusto: not prepared. |
| c2 | 2:26.4 | From missing information to payroll-ready. With you in control. |

Lines h2-h4 are short punches over the hook; say them crisply. r1 lands on the logo after the music hit.
