# Mandatory Band and Cognee capture checklist

The owner’s SF Startup Challenge brief requires a 2–3 minute video showing Band Desktop’s room, moving board, human decision, and **per-agent sessions, tokens and estimated cost**, plus a Cognee recall that changes an agent’s next action across agents or a session boundary. These are required proof, not optional B-roll. Codex-chat coordination and app usage events do not replace Band Desktop evidence.

## Current hard gap: native Band attribution

Read-only check on October 20: `band usage agents --since 2026-10-20 --until 2026-10-20 --json` returned one `(unattributed)` bucket and no product-agent-attributed rows. `band usage sessions --agent pp-audit` / `pp-resolution` / `pp-payroll`, with that date range and `--json`, each returned empty `sessions` and `agents` arrays. This does **not** prove zero sessions, tokens or cost. It establishes missing native per-agent attribution in the checked selectors. Lane C independently corroborated the missing native attribution; generic pp-audit provider/session binding fields were null. [Sanitized results](evidence/band/native-usage-status.txt). C is checking whether any actual participating native coding sessions can be attributed.

Band’s installed CLI describes usage as coding-agent, ccusage-backed **catalog estimates**, not provider billing. The generic product agents’ app OpenRouter usage events are a separate source. Never enter app figures into a Band-looking table, rename unrelated agents, invent session bindings, or narrate the unattributed bucket as product-agent cost.

**R19 remains REQUIRED GAP until the actual participating team has a native Band Desktop sessions/tokens/estimated-cost view with valid attribution.** If the team cannot obtain this before recording, tell the lead/owner the criterion remains unmet; a CLI screenshot or app usage view alone does not satisfy the mandatory Desktop view.

C subsequently reported the real room Plan attached at 14:07:02, the selected allocation case Completed while an unresolved task remains In progress, actual Audit → Resolution and correction → Payroll handoffs/acknowledgements, and the real 13:32 human decision. Use the [redacted capture guide](evidence/band/mandatory-capture-references.md); exact internal identifiers stay private with C/the owner. Desktop footage and visible mention-chip checks are still pending. Native usage attribution is still missing.

Read-only supported-path investigation and exact owner sponsor question: [native usage research](band-native-usage-research.md). No verified generic/OpenRouter → native cost-view ingestion path found; SDK `Emit.USAGE` timeline events do not yet close R19.

## Capture in this order (automatic capture chat records; Lane C validates state)

| Check | Exact evidence in Band Desktop | Accept only when |
|---|---|---|
| B1 — Same team, shared room | Open the PayrollPilot room and show at least two actual collaborating agent participants. Identify product agents versus any native coding agents by their real roles. | The visible participants performed the work shown. No unrelated room/session footage. |
| B2 — Lead plan in the room | Show the actual lead/architect message describing the shared goal, role assignments, dependency order and human decision point. Context should cover Audit → Resolution → Payroll Preparation for the selected case. | The message really exists in Band, written by the participating lead agent; a repo plan or this checklist is not proof. C/lead supplies the message reference. |
| B3 — One board, claimed work, Done | Show the same room’s task board: a real agent claims its task, dependent task moves to the next agent, work finishes, state reaches Done. Use genuine recorded transitions or visible task history. | Task/agent identities correlate to B2/B4 and the work actually happened. Do not move cards just for a visual and call that completed work. |
| B4 — Direct @handoff | Show an actual sender’s @mention to the next agent with case context, and the recipient’s acknowledgement/result. Show the referenced board item. | Agents pass context directly through Band; human copy-pasting between Codex chats is not this criterion. A name in plain text is not evidence of a routed @mention. |
| B5 — Real human decision in Band | Show `[decision.requested]`, exact batch scope, then the owner’s `approve <batch_id>` room reply and the resulting version-bound approval. Use the verified 1:32 room decision if needed, labeled PLAYBACK. | The human made the decision through Band and the backend observed it. `band ask` is unsupported for these generic peers. A UI-only approval is not the Band decision proof. |
| B6 — Native visibility (REQUIRED GAP) | In Band Desktop, open the participating agent’s native session/usage detail. Hold long enough to read **session count/list, tokens and estimated USD cost**; repeat for each participating measurable agent and show how the session belongs to that team/work. | Lane C identifies valid native bindings and the real view shows attributable data. Label missing/unattributed values accurately; no app totals or unrelated agents substituted. Estimated cost is not billed cost. |

The dedicated **Record PayrollPilot demo footage** chat owns automatic capture on `cloud/film`, writing numbered files only under `demo/film/clips/`, due **3:00 PM Pacific**. The owner only supplies phone replies through C’s single-cue coordination and foregrounds Band when requested. No human screen recording is required; E imports/cuts/renders without recording. For B2/B4/B6, C/lead provides exact mappings privately before capture. This checklist is not a request to post artificial messages or manufacture telemetry. If only a separately coordinated native coding team is measurable, identify that team and its actual PayrollPilot work honestly; the lead must decide how it satisfies the brief. Do not portray those numbers as generic product-agent usage.

## Cognee evidence, without stopping the live stack

| Check | Exact evidence | Accept only when |
|---|---|---|
| C1 — Working memory write | Show a real confirmed scoped fact written by one agent, with a sanitized evidence reference. | It is a work-derived fact, not a preloaded static document dump. |
| C2 — Other/fresh process recall | Show a second agent or separate fresh process recalling that fact. Existing cross-process proof may be shown as **PLAYBACK · earlier verified run**. | Agent/process identities and timestamps establish the boundary. Leave backend :8000 and bridge :3001 running. |
| C3 — Behavior changes | Same request/context before and after: next action changes from asking for a job to proposing an allocation; `approval_created: false`. Keep owner correction approval separate. | The recall causes the changed action and the referenced records/scope validate. Current-flow behavior change is now proven in C-07 persisted live events; separate full-response/cross-process evidence belongs to C/PR #38. Do not label the timed-out/500 identical-baseline-query HTTP attempts successful. Final capture is separate from proven runtime behavior. |
| C4 — Essential dependency | Use Lane C/F’s verified delete-test result: disabling Band blocks required coordination; disabling Cognee removes the remembered answer/changes the next action. | The exact tested route/version supports it. E does not disable a live service to film the check. A health badge alone does not prove essentiality. |

Evidence: historical cross-process `demo/evidence/cognee/recall-run.txt`; current-flow C-07 section of `INTEGRATION-FINDINGS.md` records real clarification reply/memory write and observed behavior-changing recall at 13:51/13:53, then owner application and verified workbook. Other C session’s full-response/cross-process evidence is tracked in PR #38. The documented identical-baseline-query calls timed out/returned 500 and are not successful proof. These runtime records support the claim; final video capture is still separate.

## Film allocation within the existing 2:32 cut

- `m2-band-handoff.mov` (0:35–0:42): B4 with acknowledgement and dependent board item.
- `e2-band.mov` (1:51–2:03): B1/B2/B3/B5, with only readable cuts; use earlier genuine transitions as PLAYBACK.
- **`e3-usage-recall.mov` (2:03–2:15) must become the native Band Desktop B6 view.** Current app usage events are supplementary and cannot fill this slot. Update the film’s route, title, narration and evidence status only when the actual view is verified. Do not keep the old app-metering narration over a Band view or call pending metrics proven.
- `m7-cognee.mov` (1:21–1:32): C1–C3 with appropriate REAL / SYNTHETIC / TEST REPLY / PLAYBACK labels. No live service restart.
- Product/readiness/workbook beats retain their separate stage/item blockers and “Gusto: not prepared”. Nothing submits payroll.

If readable mandatory proof needs more time, trim illustration time; stay under three minutes. Never cut mandatory Band visibility or Cognee behavior proof in favor of optional integrations.

## Capture acceptance / privacy

- [ ] Every mandatory B1–B6 and C1–C3 shot has an actual sanitized artifact path and a truthful label in the evidence matrix.
- [ ] B6 session → agent → PayrollPilot work mapping confirmed by C; unattributed is not attributed and unknown is not zero.
- [ ] B2/B4 references supplied; no claim that a shared plan or routed @handoff exists without its message/task proof.
- [ ] No phone numbers, provider space ids, credentials, private pilot identities or unrelated room/session content visible.
- [ ] Dedicated automatic capture chat records; numbered clips committed on `cloud/film` under `demo/film/clips/` by **3:00 PM Pacific**. Owner only replies on phone and foregrounds Band. E imports/cuts/renders; no duplicate or human screen recording.
- [ ] Final film reviewed end to end; final preflight passes; owner uploads by 3:15 and verifies playback/receipt before 3:30.

## Read-only checks run by Lane E

```bash
band usage --help
band usage agents --help
band usage sessions --help
band usage agents --since 2026-10-20 --until 2026-10-20 --json
band usage sessions --agent pp-audit --since 2026-10-20 --until 2026-10-20 --json
band usage sessions --agent pp-resolution --since 2026-10-20 --until 2026-10-20 --json
band usage sessions --agent pp-payroll --since 2026-10-20 --until 2026-10-20 --json
```

All exit 0. Native usage schema: agent rows have `peerName`, `sessionCount`, token categories, `totalCost`, `lastActivity`; session replies have `sessions`, `agents`, `totals`. Sanitized result: one unattributed agent bucket, zero product-attributed agent rows, empty sessions/agents for the three checked product selectors. Raw usage remains outside the public repo; no unrelated figures published. No Band state, services, message recipients or approvals changed.
