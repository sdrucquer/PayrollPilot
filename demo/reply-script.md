# Reply script for the owner's phone (test replies)

Every reply below is a **test reply**: the owner is answering on behalf of the intended respondent ("Ops lead"). The UI labels it `test_reply`; the film chip says TEST REPLY. Send replies from the phone that the PayrollPilot iMessage arrives on, in the same thread, nothing else in between.

The batch these answer (drafted by the Resolution agent; wording will differ, meaning should not). Lane C confirmed this batch at 1:05 PM: exc_611be6d68e (already_paid_allocation, te_0014) and exc_d06fba51f7 (offsite_link, job_03), one message to the ops-lead role, sent to the allowlisted owner phone:

1. The already-paid shift on Oct 1 (Worker B, 8h) is logged on Job 01 but was scheduled on Job 02. Which job was it?
2. Job 03 (the off-site disposal run) has no parent job. Which job was it for?

If lane C's demo batch covers different exceptions, use the fallback replies at the bottom and tell lane E so the narration changes.

## Before you start

- Contact for the Photon sender saved as **PayrollPilot** so no number shows in the thread header.
- Do Not Disturb on, with the Messages app allowed (or Focus off for just this thread). Notification previews: "When Unlocked".
- Phone unlocked, Messages open on the PayrollPilot thread, keyboard autocorrect is fine.
- Copy the replies into Notes on the phone so you paste, not type, if you are nervous about typos. Pasting is fine on camera.

## Sequence (final take and rehearsal are identical)

| Cue (what you see) | You send | Expect in the UI within ~10 s | Script time |
|---|---|---|---|
| B0. Before the send, Band Desktop shows `[decision.requested]` for this batch in the PayrollPilot room (`band ask` does not work for these agents). | Reply in the Band room: `approve <batch_id>` (copy the id from the message). | The app records the approval from the room (or click Approve and send in the app; either path creates the same approval record). | 0:42-0:48 |
| R0. The question batch arrives on the phone (after you click Approve + Send in the UI). | Nothing. Hold the phone steady 2 s so the camera sees the message. | Batch state `sent`, provider status shown. | 0:48-0:54 |
| R1. Wait 2 s after R0. | `yes` | Inbound labeled TEST REPLY; both questions `ambiguous`; Clarify button appears. | 0:54-0:57 |
| R2. In the UI click Clarify, review the follow-up, Approve + Send. Wait for it on the phone. | Nothing until the clarification arrives. | Clarification batch `sent` (new approval id). | 0:57-1:03 |
| R3. Clarification visible on the phone. | `The Oct 1 shift was Job 02, the patio build. The disposal run on Job 03 was for the patio job too.` | Both cases `needs_approval`: te_0014 -> job_02, Job 03 off-site for parent job_02; quote shown; Cognee stores the resolutions in the background. Mapping "patio" to job_02 needs the live OpenRouter key (lane C). | 1:03-1:10 |

Then continue in the UI: approve the correction, apply, watch the board (Beat 5).

## Do not send

- Anything with a real person's name, a dollar amount, a rate, or a phone number.
- An instruction like "pay X $500" during the take. That injection test (T17) is proven in lane F's suite, not in the film.

## Fallbacks

- **Batch has only one question:** R1 `yes` still shows `ambiguous`. R3 becomes `It was Job 02, the patio build.` Narration line 09 changes "two questions" to "a question".
- **Batch is about the missing-job shift (Sept 29, 2h14) instead:** R3 `That 2h14 on 9/29 was Job 01, the lawn install.` (matches the fixture's clean answer). Beat 5 narration must then change: a missing-job fix may change wages; check the correction's impact on screen before narrating "wages don't move".
- **Reply not parsed within 30 s:** do not resend (dedupe would ignore a duplicate anyway). Cut, check the bridge terminal off-camera, and use the rehearsal clip of R1-R3 labeled PLAYBACK.
- **No message arrives within 30 s of Approve + Send:** stop the take. Check the bridge log off-camera. Do not switch to the fake adapter on camera.
