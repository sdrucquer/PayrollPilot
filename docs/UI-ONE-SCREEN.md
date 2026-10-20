# UI decision v2 (owner, 12:58 PM): super simple. One page, three questions.

Supersedes v1 of this file and the four-route plan. Lane D ships this page; lane G mocks this page; lane E films this page. Clean, light, Apple-like (docs/DESIGN-DIRECTION.md). Nothing on the page needs a legend to read.

The owner needs three answers, in this order, with at most one action each:

## 1. Is payroll ready?
Two lines, plain language, no chips:
- **Employee wages**: "Ready for 3 of 4 workers. Worker B needs 1 answer." (from `GET /cycles/{id}/readiness` stage1)
- **Job costs and bonuses**: "1 commission ready. Tips and manager pool waiting on 2 answers and 1 decision." (from stage2 items; one sentence, each item named only if not ready)
- Under them, one quiet line: "Gusto: not prepared · Export workbook" (button).
- One agent line, small: "Audit finished 12:41 · Resolution is waiting on the ops lead · Payroll prep paused until answers arrive." (latest event per actor, rendered as a sentence)

## 2. Who do we still need answers from?
A short list grouped by person, ops lead first (he is nearly all of it):
- **Ops lead** (3): each row is a question in plain English with its state: "Which job was Worker A's Friday shift on? · answered 12:49", "Was the $40 tip on Job 03 for one person or the crew? · asked 12:44, no answer yet", "Open timer on 10/09, when did Worker D finish? · not asked yet".
- **Worker D** (1), **You** (1 decision: overhead allocation method) if any.
- One button for the group: **Send questions** (opens a sheet with the exact message and the masked recipient; Approve sends). Follow-ups use the same sheet.
- Source: exceptions grouped by intended respondent; question text is the exception's `title` rewritten as a question by Resolution; state from message/reply events.

## 3. What do I need to approve?
Only items in `needs_approval`, as one card each, one sentence plus impact:
- "Move Worker A's 10/02 shift to Job 02. Wages unchanged. Job 02 cost +$181.14." **Approve** · Ask again
- "Send 1 follow-up to the ops lead about the tip." **Approve** · Edit
Nothing else is on the page.

## Footer
One small line: "Test mode: texts go to your phone · Synthetic data · Nothing is submitted to Gusto." A **Details** link opens the full view (evidence, event log, memory recalls, blocked instructions, hashes) for judges and debugging. Lane D keeps the detailed screen it already built as that Details view; it is not the home page.

## What changes versus the screenshot the owner rejected
- No sidebar, no filters, no search, no IDs, no hashes, no provenance chips on rows, no event timeline on the home page.
- Questions are sentences, not exception records. States are three words max.
- One primary button per block. Approve actions live in block 3 only.
- Evidence and the agent trail are one click away, never on the home page.
