# PayrollPilot in one page (what it can and cannot do)

PayrollPilot prepares payroll for one home-service business. It pulls one pay period of records from Jobber, Gusto, and QuickBooks (or an owner export), audits them with deterministic checks, raises issues with evidence, texts the right person a grouped question, reads the reply, proposes a correction, recalculates, and hands the owner a review packet and a reconciled workbook. Three product agents share one model and differ by permissions: Audit finds and evidences, Resolution asks and interprets, Payroll Preparation computes and reports. A deterministic coordinator owns state and approvals.

## It can
- Detect missing, unassigned, long, overlapping, or duplicate time and mismatched or duplicated costs, each with source evidence and stage impact.
- Group questions by respondent and send a real iMessage (Photon) after the owner approves the exact text and recipient (test mode: only the owner's allowlisted phone).
- Parse a reply, flag vague, partial, or conflicting answers, and ask a bounded follow-up within the same scope.
- Propose local corrections with before/after and calculation impact; apply them only after owner approval; recalculate wages and job costs.
- Show Stage 1 wages and each Stage 2 item (quote commission, tips, manager pool) with independent readiness and named blockers.
- Export a 12-ledger review workbook with pending tabs present and totals verified against the on-screen draft.
- Hand cases between agents through a Band room with a human decision, and recall confirmed facts from Cognee to change a later action.

## It cannot
- Submit or pay payroll, write to Jobber, Gusto, or QuickBooks, or create a Gusto draft (gated, no executor).
- Invent a rate, percentage, overhead, threshold, break, or prior payment; unresolved policy is a visible blocker, never a default.
- Mark anything ready while a required input is unknown, or roll separate items up into "payroll complete".
- Text anyone other than the allowlisted owner phone, or act on instructions found in a reply, web page, receipt, or memory.
- Replace the payroll provider's tax and net-pay math, decide worker classification, or claim settlement from a screen message.

Everything shown is labeled real, cached, synthetic, seeded issue, test reply, or playback.
