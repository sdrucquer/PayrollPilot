# PayrollPilot UI design notes (lane G)

## FROZEN 1:40 PM · what lane D builds

Files: `design/home.html` (in progress, approval pending), `design/ready.html` (payroll ready), `design/idle.html` (between payrolls). Static exports, open in any browser, no runtime. Live versions with working Edit / Approve / Decide states: `design/claude-design/*.dc.html` and the canvas https://claude.ai/artifact/HUHEVg4NwowgudNWyK4djG.

### Layout
Single centered column, `max-width: 720px`, 24px side padding, 22px gap between cards. Top bar: logo + company, test-mode pill, "Gusto: not prepared" badge, Pause. Then in order: Hero card (headline + readiness lines + progress ring), the one approval/summary card (tinted, the only card with a colored ring), Progress card (stepper + current step), Activity card, one-line footer. No sidebar, no tables, no ids.

### Final tokens
| Token | Value |
|---|---|
| Page background | `linear-gradient(180deg,#F5F5F8,#EEEEF3)` (fallback `#F2F2F7`) |
| Card | `#FFFFFF`, radius `28px`, shadow `0 1px 2px rgba(0,0,0,.03), 0 20px 48px -28px rgba(20,20,40,.22), 0 0 0 1px rgba(0,0,0,.03)` |
| Inset tile | `#F5F5F8`, radius `18px`; current-step panel `#F5F8FF` |
| Approval card | background `linear-gradient(180deg,#F3F8FF,#FFFFFF 38%)`, ring `0 0 0 1.5px rgba(10,122,255,.30)`; ready variant uses green `#F3FBF5` / `rgba(31,138,59,.30)` |
| Text | primary `#1C1C1E`, secondary `#3A3A3C`, muted `#6E6E73`, faint `#8E8E93` (only at 12px+ meta) |
| Accent | `#0A7AFF`, hover `#0066D6`, tint `#E8F1FF` |
| Ready / verified | `#1F8A3B`, tint `#E6F6EA` |
| Waiting / test | `#D97A00` dot, text `#9A4D00`, tint `#FFF4E5` |
| Blocked | `#E0323F`, tint `#FDE8EA` (not used on the home page) |
| Neutral stepper segment | `#E5E5EA`; hairline `rgba(0,0,0,.05)` |

### Type (font: -apple-system, "SF Pro Display"/"SF Pro Text", Inter fallback)
Hero headline 36/700/-0.03em · hero money 48/700/-0.04em (cents 26px `#8E8E93`) · card title 18/700/-0.015em · section label 11.5–12.5/600–700/+0.06em uppercase `#6E6E73` · body 15/400 · meta 13 `#6E6E73` · timestamps 12.5–13 `#8E8E93` · tabular numerals for money.

### Buttons
All pills (`border-radius: 999px`). Primary: 48px tall, `#0A7AFF`, white 16/600, shadow `0 8px 20px -8px rgba(10,122,255,.8)`, one per screen. Secondary: 48px, white, `0 0 0 1px rgba(0,0,0,.08)`. Tertiary: transparent, `#6E6E73`. Small: 32–34px, `#1C1C1E` on dark "Decide", `#F2F2F7` on neutral. Press: `scale(.98)`.

### Components
Hero ring: 112px SVG, r=48, stroke 10, track `#ECECF1`, done arc green, current arc blue. Stepper: 6 segments 8px tall, gap 6px, a 1px divider between Stage 1 (4 segments) and Stage 2 (2); current segment pulses opacity. Message preview: contact row (28px circle initial, name, "iMessage · •••-••12") + blue bubble `border-radius: 20px 20px 6px 20px`. Activity row: 30px icon chip radius 10 (blue send/chat, green check, orange search, gray contact), text 15, time right. Test-reply tag: orange pill 11.5/600.

### Motion
Cards rise 10px/fade 550ms `cubic-bezier(.2,.7,.2,1)`, stagger 80ms. Ring draws in 1.2s. Approval avatar and current-step dot: 2.4s pulse ring. Waiting spinner: 14px ring 1s. All off under prefers-reduced-motion.

---

## Current direction (owner decision, 1:10 PM): one calm screen

The owner asked for an aggressive simplification. PayrollPilot should feel like an AI employee doing payroll in the background and only asking for approval when necessary. The primary interface is a single centered column (max 760px) with four parts, in this order:

1. **Needs your approval** (only when something is waiting): the exact drafted message, the respondent as a role with a masked number, and three buttons: Approve & send, Edit, Decline. These map to the existing contracts (POST /api/approvals with the text hash as target_version, then POST /api/messages/{batch}/send; Edit invalidates the approval and requires re-approval). Never bypass them.
2. **Progress**: six plain-English steps with completed / current / upcoming states, grouped so Stage 1 (Employee wages) and Stage 2 (Financial reconciliation) stay distinguishable: Gathering employee hours, Auditing hours, Resolving missing information, Preparing employee wages, Reconciling job expenses and commissions, Payroll ready for your review.
3. **Activity**: plain-English lines with times ("Checked 42 timesheets", "Found 3 missing job assignments", "Drafted a question for the Ops lead", "Ops lead replied", "Verified the correction", "Employee wages ready for review"). Test replies carry a small "test reply" tag.
4. **Payroll summary** (ready state): totals per item (wages, commissions & tips, manager pool), what is verified, what is left out until resolved with a Decide button, and ONE action: "Approve this draft". Copy says explicitly that this does not submit to Gusto; the top bar badge reads "Gusto · not submitted".

Removed from the main interface: multi-column layouts, exception tables, record ids and hashes, evidence panels, raw agent logs, filters and categories, per-agent pages. That detail can live behind "Show everything" or a secondary screen for the pilot team, never on the owner's home.

Sources: `design/claude-design/Main.dc.html` (approval pending, interactive: Approve & send transitions to a Sent state and adds an activity line), `Ready.dc.html` (ready state), `Phone.dc.html` (390px, the owner approves from a phone), built natively in Claude Design; canvas: https://claude.ai/artifact/55usfvGbaCVYAWY2piYaeC (private until shared). Names stay as roles (Ops lead); no personal names in committed files.

Visual language for this direction: page `#F2F2F7`, white cards radius 22px with a very soft shadow, body 15px, titles 32px/700, uppercase 12px section labels in `#6E6E73`, iOS blue `#0A7AFF` for the single primary action and the current step, green `#1F8A3B` for done/verified, orange `#B35C00` for waiting/test labels, `—` for unknown money. Buttons are 44–46px pills; the primary one is the only filled blue element on screen.

Visual system v2 (after owner feedback that v1 looked generic): a hero card anchors each screen (big status headline or the total payroll figure at 48px, plus a progress ring); progress is a horizontal 6-segment stepper with Stage 1 and Stage 2 labels and only the current step expanded; the approval is presented as a message preview from a named agent persona ("Pilot") with an avatar, the recipient shown as an iMessage contact row, and the draft as a blue bubble; the activity feed uses 30px rounded icon chips instead of dots; cards are 28px radius with a layered shadow and a 1px hairline ring; page background is a faint top-to-bottom gradient. Interactive states: Edit opens an inline edit sheet (any change creates a new version to approve); Decide opens an inline option sheet with three plain methods and no percentages.

Motion in this direction: cards rise 8px / fade in over 500ms with a 80ms stagger; the current step and the approval dot carry a slow 2s pulse ring; the Sent check pops in (scale .6 to 1); new activity lines rise in. All off under prefers-reduced-motion.

Other screens still to mock (not yet built): the approval sheet opened by Edit (exact text, masked recipient, re-approve), the decision sheet for a policy question (overhead allocation), the idle state ("Nothing needs you. Next payroll starts Oct 13"), the Details view (lane D's existing detailed screen), and a reply-arrived state on the phone.

## Earlier exploration (superseded for the owner's home; still useful for the pilot team's detail views)

Static mockups for lane D (production UI) and lane E (video). Visual reference only, not a spec to rebuild pixel-for-pixel.

- `command-center.html` — cycle overview: Stage 1 wages, Stage 2 reconciliation (quote commission, tips, manager pool as separate cards), agents, open exceptions, questions awaiting replies, next actions, "Gusto: not prepared".
- `exceptions-inbox.html` — list + detail: observed/expected, evidence refs, stage impact, respondent as a role with masked recipient, thread with agent messages and `test_reply` labels, parsed answers, T17 blocked instruction, proposed correction with before/after and version-bound approval.
- `screenshots/*-1280.png` — rendered at 1280px.

Direction: clean, Apple-like. Soft gray page, white cards with large radii and very soft shadows, almost no borders, pill controls, iOS blue as the single accent, status colors only for readiness. All data is synthetic (Worker A–D, Ops lead, Pilot Co).

## Color tokens (light)

| Token | Value | Use |
|---|---|---|
| `--bg-0` | `#F2F2F7` | page background, sidebar |
| `--bg-1` | `#FFFFFF` | cards, panels |
| `--bg-2` | `#F5F5F8` | insets inside cards (tables, tiles) |
| `--bg-3` | `#ECECF1` | chips, segmented controls, table headers |
| `--bg-hover` | `#E8E8EE` | hover on neutral buttons |
| `--line-1/2/3` | `rgba(0,0,0,.05/.08/.14)` | hairlines only; most cards have no border |
| `--fg-0` | `#1C1C1E` | primary text |
| `--fg-1` | `#3A3A3C` | secondary emphasis |
| `--fg-2` | `#6E6E73` | body/secondary |
| `--fg-3` | `#8E8E93` | labels, meta, ids |
| `--accent` | `#0A7AFF` | primary actions, selected state, agent bubbles |
| `--accent-strong` | `#0066D6` | hover |
| `--accent-dim` | `rgba(10,122,255,.10)` | approval panel background, accent pills |
| `--ready` / `--ready-dim` | `#2DA44E` / `rgba(52,199,89,.13)` | Readiness `ready` |
| `--partial` / `--partial-dim` | `#D97A00` / `rgba(255,159,10,.14)` | Readiness `partial`, awaiting reply, seeded issue, test mode |
| `--pending` / `--pending-dim` | `#8E8E93` / `rgba(142,142,147,.14)` | Readiness `pending`, detected/investigating |
| `--blocked` / `--blocked-dim` | `#E0323F` / `rgba(255,59,48,.10)` | Readiness `blocked`, escalated, blocked instruction |
| `--info` / `--info-dim` | `#5E5CE6` / `rgba(94,92,230,.10)` | synthetic/fixture provenance, cost category |

Readiness state → color is the only semantic color mapping in the UI. Never use green for anything that is not `ready`. Copy rules from docs/PRODUCT-STATEMENT.md: no "payroll complete", no "automatic"; every send and correction shows an owner approval; unknown stays `—` and is a blocker.

Provenance (dot + label, always visible, low contrast): `real` green, `cached` gray, `synthetic` indigo, `seeded_issue` orange, `test_reply` blue, `playback` gray (replayed scripted replies). Test mode is an orange outlined pill in the top bar on every screen.

## Type

Font: `-apple-system, "SF Pro Text", Inter, system-ui`. Mono: `ui-monospace, "SF Mono", JetBrains Mono` for money, minutes, ids, hashes. Tabular numerals on.

| Role | Size / weight / tracking |
|---|---|
| Page title (cycle, exception title) | 24px / 700 / -0.022em |
| Stat value | 20px / 700 / -0.02em (mono for money) |
| Card title | 13px / 600 |
| Section label (S1 EMPLOYEE WAGES, OBSERVED) | 10.5–11px / 600 / +0.07em uppercase, `--fg-3` |
| Body | 13.5px / 400, 1.45 line height |
| Secondary / meta | 11.5–12px, `--fg-2` or `--fg-3` |
| Mono values | 12–12.5px |

Money: `$1,848.00`, unknown is `—` in `--fg-3`, never `$0`. Minutes shown as integers in tables (`5,040`) and as `2h 14m` in prose.

## Spacing and shape

- Base unit 4px. Card padding 16px (hero 18–20px). Grid gap 18px. Content gutter 24px.
- Radii: `--r-sm` 10px (inputs, small boxes), `--r-md` 14px (inset tiles, rows), `--r-lg` 20px (cards), pills 999px.
- Shadows: `--shadow-1` `0 1px 1px rgba(0,0,0,.04), 0 1px 3px rgba(0,0,0,.05)` (chips, selected nav, dest badge); `--shadow-2` `0 1px 2px rgba(0,0,0,.03), 0 10px 30px -14px rgba(20,20,40,.14)` (cards).
- Sidebar 224px on overview screens; 64px icon rail on the inbox so list (336px) + detail fit 1280.
- Desktop target 1280px; app shell is `grid-template-columns: 224px 1fr`.

## Components

- **Top bar**: breadcrumb, test-mode pill, provenance pill, destination badge (`Gusto: not prepared` with lock), stop-run ghost button, primary action.
- **Pill** (`.pill`, `.mini`): status with dot; variants ready/partial/pending/blocked/accent/info/test.
- **Provenance label** (`.prov`): dot + lowercase text.
- **Stat tile**: label, value, sub line.
- **Coverage chip**: dot (ok/warn) + system + dataset + mono count/method.
- **Next actions**: numbered blue circle, title, one-line why, chevron. Disabled "Submit payroll · unavailable" with lock.
- **Stage card**: `S1`/`S2` key + uppercase label, status pill, one-line summary listing each item separately, body, 3 indicator footers (wage correctness / labor-revenue / cash confirmation; never the word "complete").
- **Worker readiness table**: avatar, name + rate status, minutes, gross (mono, `—` when null), readiness pill; progress bar under it.
- **Compensation item card** (quote commission, tips, manager pool): colored left rail by readiness, title + pill, scope, amount (right, mono, `—` + "unknown amount"), blocker list with `code` chips (`policy_missing:overhead`).
- **Agent card**: icon, name, one-line progress, live dot (green pulse = working, orange = waiting, gray = done), progress bar, usage row (model, in/out tokens, cost) or "no LLM".
- **Exception row**: category square (orange wages, indigo costs, red blocked), title, subtitle with category · entity · respondent role · masked recipient, dollars + impact, state pill, chevron.
- **Inbox list**: search, filter chips (selected = black pill), groups (Needs you / Awaiting reply / Investigating / Blocked input / Resolved), selected row white with blue left edge.
- **Observed / Expected** boxes; **impact tiles** (dollars, stage 1, stage 2); key-value list; **evidence rows** (system badge J/G/Q, label, mono ref, link or "no link").
- **Thread**: system lines (handoff, memory recalled/applied), agent bubbles blue with tail, human bubbles gray, draft bubbles dashed, blocked bubble red inset ring with `<mark>` on the instruction and a "blocked instruction" explanation row; parsed-answer rows (answered / partial / ambiguous / unaddressed + confidence).
- **Correction**: before/after columns (after has green border), deltas list, approval panel (lock icon, kind, scope text with target version hash, Approve & apply / Ask again / Reject, note that data changes invalidate the approval).

## Animation (keep subtle)

- Cards: fade + 6px rise, 550ms `cubic-bezier(.2,.7,.2,1)`, staggered 50–70ms. Implemented as `body.anim .card` and removed after 1.2s so the settled page has no animation state (safe for screenshots and video freeze-frames).
- Progress bars: width transition 1.1s same easing, set from `--w` after first paint.
- Live agent dot: 1.6s ping ring; waiting dot slower (2.4s); test-mode dot gentle 1.8s opacity pulse.
- Hover: 150ms background/border only; buttons translate 1px on press.
- `prefers-reduced-motion`: all animation off, bars at final width.

## Adoption tips for lane D

Copy the `:root` block as CSS variables (or Tailwind theme colors) and the `.pill`, `.btn`, `.card`, `.item`, `.exc` rules; they are plain CSS with no dependencies. Both files share the same head, so diff them to see only inbox-specific rules.
