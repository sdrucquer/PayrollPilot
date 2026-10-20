# PayrollPilot product brief (public, sanitized)

This is the public one-page summary. It contains no real names, phone numbers, pay rates, or allocation percentages, and it was written from the repository's shared context, contracts, and architecture, not from the private requirements document.

## Problem

A small home-service business runs payroll every two weeks from three or more tools that do not agree: a field-service app for time and jobs, a payroll provider, and accounting plus bank feeds. The owner reconciles them by hand in a spreadsheet. Payroll often looks complete while the records underneath are not: a shift with no job, a paid shift logged to the wrong job, an open timer, a duplicate profile, a receipt nobody can place, a commission whose quoter is unclear. The usual fixes are guesses: trim the hours, assume the break, pay it anyway.

## Who it is for

One owner-operated business with a small crew, an operations lead who knows what happened in the field, and an owner who approves money. First pilot: one company, shown de-identified as "Pilot Co".

## What PayrollPilot does

1. **Loads one pay period** from an authorized, read-only snapshot and records where each record came from and how complete each source was.
2. **Audits deterministically**: missing or wrong job, long shifts for review, open timers, overlaps, duplicates, identity problems, unconfirmed rates, already-paid shifts on the wrong job, unmatched or conflicting costs, off-site jobs with no parent, unclear quote attribution, coverage gaps. Each exception carries evidence and its impact on wages versus job costing.
3. **Asks the right person**: groups questions by respondent, drafts one message, and sends it only after the owner approves the exact text and recipient.
4. **Interprets replies**: each question is marked answered, partial, ambiguous, conflicting, or unaddressed. A vague "yes" gets a bounded clarification, never an assumption. Instruction-like replies are blocked.
5. **Proposes local corrections** with before/after and calculation impact. The owner approves each one. Source systems are never written.
6. **Shows scoped readiness**: Stage 1 (wages) per worker, and each Stage 2 item (quote commission, tips, manager pool) separately, with blocker codes. Nothing rolls up to "complete".
7. **Remembers confirmed facts** so the next time a related record appears, a restarted agent proposes the known answer instead of asking again; memory never grants approval.
8. **Exports** a review packet and a reconciliation workbook whose totals are verified against the packet. The destination is labeled honestly: "Gusto: not prepared".

## Principles

- The owner approves every effect. Approvals bind to exact content.
- Money in integer cents, time in minutes, unknown is null. Missing policy is a visible blocker, never a default.
- Agents propose; a deterministic coordinator decides what changes.
- Everything shown is labeled: real, cached, synthetic, seeded issue, or test reply.

## Not in this pilot

Payroll submission, payroll-provider drafts, writes to source systems, texting crew members directly, multiple companies, billing.

## Measures of success for the pilot

- Every exception in a period is either resolved with evidence or shown as a named blocker.
- No question is sent without an exact-text approval; no correction applies without its own approval.
- Time from "period closed" to "review-ready packet" falls, and the owner stops re-asking questions the business already answered.
