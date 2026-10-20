# PayrollPilot

**Your AI payroll team. From missing information to payroll-ready, with you in control.**

PayrollPilot is an AI-powered payroll operations team that actually understands your business. It learns your company's workflows, employees, pay structures, job history, and financial rules. Its agents proactively audit timesheets and expenses, catch discrepancies, and contact the right people to resolve missing information. Powered by Band's multi-agent coordination, Cognee's persistent company memory, and protected by Snyk's security scanning, PayrollPilot gets smarter with every payroll cycle, turning hours of manual reconciliation into a streamlined, secure, owner-approved process.

## The problem

In a home-service business, payroll looks complete while the records are not. Shifts have no job, timers stay open, receipts are uncategorized, and the totals in Jobber, QuickBooks and Gusto don't agree. The owner spends payday chasing the crew and the ops lead by text to work out what actually happened, then fixes job costs and commissions by hand.

## What PayrollPilot does

It pulls one pay period from Jobber, Gusto and QuickBooks (or an owner export) and audits it with deterministic checks: missing, unassigned, long, overlapping or duplicate time, and mismatched or duplicated costs, each with source evidence and its impact on wages or job costing. It groups the open questions by the person who can answer them and drafts one message. Only after the owner approves the exact text and recipient does it send a real iMessage (Photon; in test mode, only to the owner's allowlisted phone). It reads the reply, flags vague or partial answers, and asks one bounded follow-up. It proposes local corrections with before and after values and their calculation impact, applies them only after owner approval, and recalculates. The owner gets Stage 1 wages and each Stage 2 item (commission, tips, manager pool) with separate readiness and named blockers. PayrollPilot never submits payroll and never writes to the source systems.

## The agent team

Three product agents run on one model and differ only in their permissions:

- **Audit** (`pp-audit`) finds and evidences issues. It cannot message anyone.
- **Resolution** (`pp-resolution`) drafts questions, requests the owner's decision, interprets replies and proposes corrections.
- **Payroll Preparation** (`pp-payroll`) recomputes wages and job costs and builds the review.

A deterministic coordinator owns state, approvals and every effect. LLM output is a proposal that passes a schema and the coordinator before anything changes.

**Handoffs in Band.** The agents and the owner share one Band room. Audit hands a case to Resolution with an @mention ("@pp-resolution please take this case"), and Resolution acknowledges (`[handoff.accepted]`). Resolution posts `[decision.requested]` to the owner, who answers in the room ("approve msg_batch_…"). That reply is recorded as an approval only through the backend approvals route, bound to the text hash. After a correction is applied, Resolution hands off to @pp-payroll, which acknowledges and recomputes readiness. Cases are tracked on the room's work board from To-do to Done. Band's usage view shows sessions, tokens and estimated cost; today that view is unattributed coding-session usage, and product-agent model cost is recorded from PayrollPilot's own usage events.

**Build team.** PayrollPilot was built by parallel Claude Code and Codex sessions working in separate lanes, one branch per lane, merged by a lead. The Band-coordinated build-team view was not captured for the video.

## Memory with Cognee

When an answer is confirmed (for example, "Job 03's off-site disposal run belongs to Job 02"), Resolution writes the resolved fact to a Cognee dataset scoped to the company and cycle, with references to the resolution, job and inbound message ids. Later, a fresh Payroll Preparation process recalls it (Cognee `CHUNKS` search). Deterministic code validates the ids, company scope and parent job before the recall can change anything. In the verified runs, the next action for a later Job 03 cost changed from "ask ops lead which job" to "propose allocation to job_02 pending owner approval", with `approval_created: false`. Memory can change what an agent proposes; it can never grant an approval. With memory off, the case keeps asking.

## Sponsor tools

- **Band**: shared product room with three agents and the owner, @mention handoffs and acknowledgements, a human decision in the room, the work board, and the usage and estimated-cost view.
- **Cognee**: memory write and recall across processes, changing an agent's next action without creating an approval.
- **Snyk**: Snyk Open Source CLI scan of the web app's dependency lockfile (`tests/security/snyk-web-summary.json` on main). Production dependencies came back clean; including dev dependencies, one high-severity finding (picomatch ReDoS via Vite) has no upgrade or patch available yet and is kept open. This covers frontend dependencies only.
- **Flexprice was not used.**
