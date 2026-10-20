# UI decision (owner, 1:20 PM): one screen, three zones

Supersedes the four-route plan in docs/plans/D-ui-frontend.md for what ships today. Lane D keeps anything already built that maps onto a zone; nothing else gets built. Lane G mocks exactly this screen. Lane E films one evolving frame.

Question the screen answers: **where are the agents in this payroll cycle, and what is limiting payroll?**

## Zone 1: Cycle progress strip (top, the hero)
- Pipeline for the selected period: Collect -> Audit -> Resolve -> Prepare -> Review. Each step shows the agent on it now (Audit / Resolution / Payroll Prep), its last action (from the latest event), and a timestamp. Source: `GET /api/events` (latest per actor) and `GET /api/cycles/{id}` stage states.
- Two readiness rows that never merge:
  - Stage 1 wages: `StageState.scope_note` ("review-ready for 3 of 4 workers; 1 unresolved"), expandable into the per-worker table from `GET /api/cycles/{id}/packet` (minutes, rate status, gross or dash).
  - Stage 2 items: three chips, Quote commission / Tips / Manager pool, each `Readiness.state` with its first blocker label. Source: `GET /api/cycles/{id}/readiness`.
- Chips: destination `Gusto: not prepared`; provenance of the loaded data (synthetic / real read); messaging mode (live Photon / test mode) with masked recipient; coverage summary (N datasets, M incomplete).
- Header actions: Export workbook (`POST /api/cycles/{id}/workbook`, shows draft version and "original not updated"), Stop (`POST /api/run/stop`).

## Zone 2: What's limiting payroll = who we're waiting on (left, main list)
Owner refinement (1:25 PM): most blockers are missing information from the crew, chiefly the operations lead (job manager). The list is organized by **respondent**, not by exception category.
- Groups in order, each with a count and a one-line summary:
  1. **Ops lead** (intended_respondent_role ops_lead): the bulk. "4 questions, 1 message awaiting reply since 1:32 PM". Rows are the questions in plain language ("Which job was the 8h14m shift on 10/02?"), with the evidence ref, what it blocks (wages for Worker B / job costing on Job 02), and state (draft / sent, awaiting reply / answered / needs clarification / resolved).
  2. **Workers** (role worker): identity or onboarding facts, usually few.
  3. **Owner (you)** (role owner): rate confirmations, correction approvals, and policy decisions (O-ids). These are decisions, not questions; the row's action is Approve or Decide, never a text.
  4. **Resolved this cycle**: collapsed, count only.
- Group header action for Ops lead: **Draft one message** (batches all unsent questions for that respondent into one MessageBatch, opens zone 3 for approval). Questions keep separate exception ids inside the batch.
- Each row keeps provenance and "dollars affected or unknown". Policy blockers in the Owner group show the open decision id and block only the item they affect (chip in zone 1 links down to the row).
- Source: `GET /api/cycles/{id}/exceptions` grouped client-side by intended_respondent_role; message state from each exception's message_ids.

## Zone 3: Selected blocker panel (right)
- Thread for the selected exception from `GET /api/exceptions/{id}`: observed vs expected, evidence; drafted question (exact text, masked recipient, linked issue ids) with **Approve and send** (POST /api/approvals kind message_send with target_version = text_hash, then POST /api/messages/{id}/send); inbound replies labeled test reply with per-question parsed status; **Clarify** when any status is ambiguous/partial; proposed correction with before/after and calculation impact and **Approve correction** then **Apply** (POST /api/approvals kind local_correction with the correction's target_version, then POST /api/corrections/{id}/apply).
- After apply: zone 1 readiness updates for the affected item only; the row in zone 2 moves to resolved.
- Blocked-instruction badge when an event `blocked.unauthorized_instruction` references this exception.

## Removed
Separate /activity, /review, /inbox routes as destinations. Activity becomes the strip's last-action text plus a collapsible log under zone 1. Review packet becomes the Stage 1 expansion. The workbook panel becomes the header button and a toast with the artifact summary.

## Visual register
docs/DESIGN-DIRECTION.md: black/violet canvas, glass cards, the progress strip is the single glowing focal element, quiet chips for honesty labels, tabular numerals, 1280px first.
