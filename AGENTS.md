# PayrollPilot coding-agent rules

Applies to every Claude Code and Codex session working in this repository.

## Document precedence
1. Financial rules in the owner's PRD (private copy at `docs/private/PRD.md`; sanitized summary in `docs/PRODUCT-BRIEF.md`). Never edit them to make a test pass.
2. `docs/plans/00-shared-context.md` (clock, stack, ownership, safety rules).
3. `docs/contracts/CONTRACTS.md` (shapes, states, routes, events). Lead-owned.
4. Your lane plan in `docs/plans/`.
5. `INTEGRATION-FINDINGS.md` for what is actually tested vs unverified.

## Ownership and branches
- Work only in your lane's paths (shared context section 4). Shared files (`CONTRACTS.md`, `backend/payrollpilot/contracts.py`, `pyproject.toml`/`requirements.txt`, `web/package.json` lockfile, migrations/db schema) are single-writer: lead, or the lane the lead named.
- One branch per lane in its own worktree. Small PRs, one task ID each, title `X-NN: ...`. Lead merges. No force-push, no history rewrite, no edits to another lane's files.
- Never reset, delete, or overwrite uncommitted work you did not create.

## Coding rules
- Money: integer cents. Time: integer minutes. Unknown: `null`, never 0. `Decimal` for arithmetic, round once at the end.
- Business logic lives in `core/payrollpilot_core/` as pure, tested functions. API routes are thin. The UI never computes money.
- LLM output is a proposal. It passes through a pydantic schema and the deterministic coordinator before anything changes state.
- Every effect checks `permissions.py`. Recipient allowlist, approval version binding, and the submit prohibition are code, not prompt text.
- Every record carries `provenance`. Fixtures are `synthetic`; seeded demo issues are `seeded_issue`; owner replies in test mode are `test_reply`.
- Keep provider adapters swappable via env; business contracts never change when an adapter changes.
- Python: type hints, `pytest`. TypeScript: strict mode. No new languages, databases, or frameworks beyond the shared-context stack without lead approval.

## Secrets and privacy
- No keys, phone numbers, cookies, tokens, or MFA codes in code, prompts, commits, PR text, Band messages, screenshots, or video. Env files only; `.env.example` lists names.
- Real pilot data lives under `data/private/` and `docs/private/` (gitignored). Committed fixtures are synthetic and de-identified (`Worker A`, `Pilot Co`). Named allocation percentages stay out of committed files; code reads them from a private policy file at runtime and tests use placeholder splits.
- Send the minimum to models and memory. No tax IDs or bank data in ordinary audit work.

## Tests and reporting
- Every task ships with its test or an explicit "unsupported, blocked in code" test.
- Report actual commands and actual results. Never write a passing result for a test you did not run. Integration errors are not completions.
- Status format is in shared context section 7. Append your status to the "Status log" at the bottom of your lane plan.

## Prohibited
- Rewriting or weakening any financial policy, readiness rule, or permission check to pass a test or to make a card green.
- Inventing rates, percentages, overhead, thresholds, prior payments, or "assumed" breaks.
- Simulating Photon, Band, or Cognee and labeling it real. Fakes exist for local development and must say so in `/api/health` and on screen.
- Implementing source writes or payroll submission (gated P1; no executor in this pilot).
