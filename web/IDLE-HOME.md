# Between-payrolls home

`/preview/between-payrolls` is an explicit **design preview** of the owner's “Home · between payrolls-html.zip”. All dates, money, approval/submission history and connection statuses on that route are synthetic values transcribed from the ZIP. They are never an API fallback. Its banner says “Design preview · Synthetic scenario · No live actions”; scheduling and workbook controls are disabled. Details and Return to current payroll are working navigation links.

The native React implementation follows the ZIP's type, spacing, colors, ring, shadows and four-card layout. At 1280px the cards retain the reference's exact bounds; at phone widths they stack without horizontal overflow. The supplied ZIP's illustrative weekday/date wording is retained only in the synthetic preview. Production presentation comes entirely from an explicit payload.

## Production integration seam

The current backend has **no idle lifecycle/schedule provider**, so ordinary API mode remains on the existing approval home. No backend, financial rule or shared contract was added for this view.

When a future provider supplies `idle_home` on the cycle response, `/` can show it only after successful data loading, with no stopped run, no unresolved exception and no pending message or local correction (including batches attached to resolved exceptions). Missing/invalid metadata and loading errors retain the existing active/error view. Pending approvals always take precedence. Historical approval text additionally requires the existing cycle's `stage1.state = owner_approved`; historical Gusto submission text requires `destination = submitted_verified | paid_verified`.

The web-only `IdleHome` schema in `src/idle-state.ts` defines the explicit presentation data:

- `state: between_payrolls`, `company_label`, `provenance`.
- `next`: supplied pay-period/payday/start labels, nonnegative `days_until_start`, summary.
- `last`: supplied period label, integer `gross_cents | null`, summary, nullable verified approval/submission/waiting labels, nullable `workbook_url`.
- `connections`: system, label, supplied status, verified flag.
- `recent`: id, icon (`check | workbook | clock`), text, date label.

No money is summed in the browser. Unknown money stays `—`. Production scheduling controls remain visibly unavailable. Download is enabled only for a supplied same-origin `/api/` download URL; disk paths and external/script URLs are refused. The current workbook-generation endpoint does not provide a download URL, so the view does not pretend it downloaded a file.

## Verification

From `web/`:

```sh
VITE_DATA_MODE=api npm run build
npm run check:contracts
node --import tsx scripts/check-home-state.ts
node --import tsx scripts/check-idle-state.ts
PP_PLAYWRIGHT_MODULE=<installed-playwright> node --import tsx scripts/check-idle-browser.mjs
```

For the source-ZIP comparison, also set `PP_IDLE_REFERENCE_HTML` to a static HTML extraction of the supplied artboard and `PP_SHARP_MODULE` to the installed sharp module. The reference runtime is not shipped or executed by the app. Comparison excludes the separate preview banner. Existing `scripts/check-home-browser.mjs` runs against an isolated FakeMessaging API and refuses a live bridge; it verifies exact-version message/correction approvals, edits, persisted declines, pause/resume, error recovery, mobile and Details.
