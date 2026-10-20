# Launch prompts and setup steps

Order the lead used on 2026-10-20: A, B, C (12:31 PM, started from the lead's Claude Code session as linked sessions in worktrees), then D, E (12:34 PM). F runs in Codex. The optional design chat is only worth opening if lane D asks for a spec.

## Band setup for Claude Code sessions (verified 12:45 PM)
The Band app's "Claude Code integration" needs the standalone `claude` CLI with a plugin manager on PATH. The desktop app alone does not provide it. Done by the lead:
```bash
npm install -g @anthropic-ai/claude-code      # installs /opt/homebrew/bin/claude (2.1.304)
export PATH="$HOME/.local/bin:$PATH"          # also appended to ~/.zprofile
band plugin install                           # installs band-peer plugin v0.5.33 into ~/.claude/plugins
band preflight                                # all rows [ok]
```
Sessions started after the plugin install load it. Inside a session: `band setup check --host claudecode --host-pid "$PPID"`. Restart older sessions to get automatic message delivery. Codex: Band lists a native Codex host under Settings > Integrations; enable it there when creating a local agent.

## Common preamble (every lane prompt begins with this)
> You are Lane <X> for PayrollPilot. Read fully, in order: AGENTS.md, docs/plans/00-shared-context.md, docs/contracts/CONTRACTS.md, then your plan docs/plans/<X>-*.md (A and C also read ARCHITECTURE.md and INTEGRATION-FINDINGS.md). Work only on your branch in your own worktree. Own only the paths your plan lists; request other changes in PR text. Development agents (us) are separate from product agents (code in backend/payrollpilot/agents/). Money is cents, time is minutes, unknown is null; never invent a financial policy. Commit small, push, one PR per task titled "<X>-NN: ...", status block (shared context section 7) in the PR and in your plan's Status log. Report only tests you actually ran, with real output. Done means acceptance checks passed. End your turn with a status block when a task is Done or blocked.

## Lane prompts
The full prompts used for A, B, C, D, E are the lead's session briefs (same content as the preamble plus the "first task" lines below). To relaunch manually from a terminal:
```bash
cd ~/Development/Hackathons/PayrollPilot
git worktree add ../PayrollPilot-<x> -b lane/<x>-<name> main
cd ../PayrollPilot-<x> && claude      # or: codex
```
Then paste the preamble plus the lane line:
- **A:** "First task A-01, then A-02. A-03 only when BROWSER_USE_API_KEY and confirmed cycle dates exist; otherwise A-04 shells first."
- **B:** "First task B-01; push the five fixture files within 15 minutes before finishing tests, then B-02, B-03, B-05, B-04."
- **C:** "First message: list the three owner prerequisites (Photon phone on account; OPENROUTER_API_KEY + LLM_API_KEY; PP_TEST_RECIPIENT in both .env files). Then C-01, C-03, C-02, C-04, C-05 with the plan's timeboxes; record every proof in INTEGRATION-FINDINGS.md."
- **D:** "First task D-01 in fixture mode, then D-02, D-03. Merge main every 15 minutes to pick up fixtures and API."
- **E:** "First E-01 and E-02, then E-03 continuously, E-04 by 2:30 PM, E-05 with the owner from 2:45 PM. Never claim to have recorded or submitted."

## Lane F (Codex) prompt
```
cd ~/Development/Hackathons/PayrollPilot && git worktree add ../PayrollPilot-f -b lane/f-qa main && cd ../PayrollPilot-f && codex
```
Paste:
> You are Lane F (QA and integration) for PayrollPilot, a hackathon build due 3:30 PM Pacific today (feature freeze 2:45 PM). Read fully, in order: AGENTS.md, docs/plans/00-shared-context.md, docs/contracts/CONTRACTS.md, INTEGRATION-FINDINGS.md, then docs/plans/F-qa-integration.md. Work on branch lane/f-qa in this worktree. Own only tests/integration/, core/tests/test_f_*.py, backend/tests/test_f_*.py, scripts/f_*.sh. Review other lanes' PRs on GitHub (sdrucquer/PayrollPilot) with comments only; never edit their files. Execute F-01 now against the fixtures on main (if docs/contracts/fixtures is empty, write the tests from CONTRACTS.md and mark them pending), then F-02 with xfail markers that you flip as code merges (run `git fetch origin && git merge origin/main` every 15 minutes), then F-03 rehearsal at 1:50 PM and 2:20 PM with the transcript in tests/integration/REHEARSAL.md, then F-04 privacy sweep at 2:35 PM. Report only commands you ran and their real output; never record a pass for a test that did not run. One PR per task titled "F-NN: ...", status block (shared context section 7) in each PR and in your plan's Status log.

## Optional UI design chat (Claude.ai, no repo access)
> You are producing a component and layout specification for PayrollPilot's frontend, implemented by another engineer in Vite + React + TypeScript. Do not write an application; write a one-page spec: four screens (cycle board; exception inbox + thread; agent activity feed; review/approval with workbook panel), the components each needs, states for Readiness (ready, partial, pending, blocked, not_meaningful) with blocker lists, provenance badges (real, cached, synthetic, seeded issue, test reply), an approval dialog that shows exact message text, a masked recipient, and linked issue ids, and a top strip showing integration modes (messaging, memory, Band). Calm, dense, readable at 1280px and phone width. Plain CSS tokens (8 colors max, one font stack). No marketing page, no branding, no animation. Output markdown the engineer can paste into web/DESIGN.md.

## Demo/video chat
Lane E runs as a Claude Code session in the repo (prompt above). If a separate chat without repo access is used instead, paste DEMO-PLAN.md and ask for `demo/script.md`, `demo/shot-list.md`, `demo/reply-script.md`, `demo/redaction-checklist.md`, `demo/submission.md` as copy-pasteable files, labeled real/synthetic/playback per DEMO-PLAN.
