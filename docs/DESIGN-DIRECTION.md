# Design direction (owner-supplied references, 1:10 PM)

Visual references the owner shared (described, not committed; do not reproduce the source art):
1. **Apple "Wonderlust" key art**: near-black background, a single hero mark rendered as fine particles/grain with a cool-to-warm gradient (steel blue to sand), particles dissolving off one edge, one word of quiet sans-serif type below. Takeaway: one luminous focal object on black, grain texture, restraint.
2. **Linear "Built for scale" tile**: deep violet-black canvas, glassy rounded tiles with 1px inner borders and soft inner glow, muted UI screenshots inside tiles, a single bright orb accent, large thin headline. Takeaway: glass panels, violet/indigo accent, dense but calm product UI inside cards.
3. **"What PayrollPilot's UI should look like" page** (owner's five-screen brief):
   1. Command Center, the home screen: overview of the payroll cycle: hours verified, missing information, employee wages, financial reconciliation, overall readiness.
   2. Exceptions Inbox, the most important screen: missing hours, incorrect job allocations, unmatched expenses, questionable shifts, and the person responsible for answering.
   3. AI Conversations: messages PayrollPilot drafts and sends, incoming responses, whether questions are resolved, proposed record corrections.
   4. Agent Activity: agents collecting information, auditing records, requesting clarification, preparing payroll; each action has a status and evidence.
   5. Payroll Review: two distinct sections, verified employee wages and additional compensation (commissions, tips, manager splits), each with readiness and approval controls.
   Centerpiece: the transition from AI detecting a problem, to a human answering it, to payroll becoming ready.

## How lanes use this
- **Lane G (mockups)**: Command Center first, in this register: black/violet canvas, glass cards, one glowing focal element (the cycle readiness), grain only in hero/title areas, thin large headline, tabular numerals. Keep the required honesty elements (provenance badges, "Gusto: not prepared", masked test recipient) styled as quiet chips, never hidden.
- **Lane D (implementation)**: adopt tokens (canvas, card, border, accent, text scale) from design/DESIGN.md when it lands; keep the four routes already planned, mapping the owner's five screens as: Command Center = `/`, Exceptions Inbox + AI Conversations = `/inbox` and `/inbox/:id`, Agent Activity = `/activity`, Payroll Review = `/review`. Do not rebuild; restyle.
- **Lane E (film)**: title card and transitions in the Wonderlust register (particle mark on black, one word), product sections in the Linear register. "Overall readiness" in narration must still be stated per stage and per item, never as one "complete" number.
