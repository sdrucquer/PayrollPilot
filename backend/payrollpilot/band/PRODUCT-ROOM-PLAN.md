# PayrollPilot product-agent lead plan

Lead: pp-audit. Room: PayrollPilot Cases.
Data: synthetic demo cycle cyc_synth_v1. Test messages go only to the owner's allowlisted phone. No source writes or payroll submission.

1. pp-audit audits the cycle and posts a minimized case with a direct @sdrucquer/pp-resolution handoff. The shared board holds the case; Resolution must receive, acknowledge, claim and start it before drafting.
2. pp-resolution drafts a bounded question, publishes an owner decision request in this room, and waits for a real human approval through the backend approval path. An edited message needs fresh approval.
3. After a real phone reply, Resolution records evidence and proposes a local correction. The owner approves and applies it in the app; the app recalculates wages/job costs without source writes.
4. pp-resolution directly @mentions @sdrucquer/pp-payroll with the APPLIED correction. Payroll must receive/acknowledge it before the corresponding shared-board task is marked complete.
5. Payroll recalls scoped Cognee resolutions for later work and proposes the next action pending owner approval. Export a review packet/workbook while preserving genuine blockers.

## Actual checkpoint

- Board #3: exc_611be6d68e, already-paid allocation. Owner applied corr_a647520203 at 13:58:06 Pacific. Wages delta 0; job costing moves 20000 cents from job_01 to job_02. Payroll handoff/board completion must be evidenced separately after this applied event.
- Board #4: exc_d06fba51f7, off-site link. Owner's real clarification produced res_d7e3b72dae39, stored by Cognee; later recall changed a proposed next action. Do not mark this board item complete merely because memory exists.
- Human room approval for msg_batch_95601f6f3ab8 was recorded at 13:32:23 Pacific. Clarification msg_batch_53be61bf427b used web UI approval at 13:44:03.
- Review workbook wb_3f0f6afb8c is verified, synthetic, 13 sheets, original_updated false. Other readiness blockers remain.
- Native Band generic peers have live host sessions but no attributed native token/cost rows. App OpenRouter events are separate and are not Band-native usage proof. That criterion remains unavailable until supported attribution is demonstrated.
