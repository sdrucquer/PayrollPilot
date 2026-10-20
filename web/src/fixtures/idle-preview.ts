import type { IdleHome } from '../idle-state'
// Values transcribed from the owner's ZIP. Design preview only, never API fallback.
export const idlePreview: IdleHome = {
  state: 'between_payrolls', company_label: 'Pilot Co', provenance: 'synthetic',
  next: { period_label: 'Oct 12 – Oct 25', payday_label: 'Fri Oct 31', starts_label: 'Monday, Oct 26', days_until_start: 6,
    summary: "I'll gather hours from Jobber that morning, audit them, and only text you if something is missing. Nothing to do until then." },
  last: { period_label: 'Sep 28 – Oct 11', gross_cents: 757000, summary: '4 employees · 3 jobs · 2 questions answered by the Ops lead',
    approved_label: 'Draft approved by you · Oct 15', submitted_label: 'Submitted in Gusto by you · Oct 16', waiting_label: 'Manager pool still undecided', workbook_url: null },
  connections: [
    { system: 'jobber', label: 'Jobber', status: 'Checked 2h ago', verified: true },
    { system: 'quickbooks', label: 'QuickBooks', status: 'Expenses partial', verified: false },
    { system: 'gusto', label: 'Gusto', status: 'Rates, read only', verified: true },
  ],
  recent: [
    { id: 'preview-approved', icon: 'check', text: 'You approved the Sep 28 – Oct 11 draft', date_label: 'Oct 15' },
    { id: 'preview-workbook', icon: 'workbook', text: 'Saved the review workbook, draft 3', date_label: 'Oct 15' },
    { id: 'preview-scheduled', icon: 'clock', text: 'Next payroll scheduled to start Monday, Oct 26 at 7:00 AM', date_label: 'Oct 15' },
  ],
}
