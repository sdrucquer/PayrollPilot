import { z } from 'zod'
import type { Data } from './home-state'
import { findPending } from './home-state'

// Optional presentation data, separate from payroll contracts. The current API does
// not supply this envelope; absence always preserves the active approval home.
export const IdleHome = z.object({
  state: z.literal('between_payrolls'),
  company_label: z.string(),
  next: z.object({ period_label: z.string(), payday_label: z.string(), starts_label: z.string(), days_until_start: z.number().int().nonnegative(), summary: z.string() }),
  last: z.object({ period_label: z.string(), gross_cents: z.number().int().nullable(), summary: z.string(), approved_label: z.string().nullable(), submitted_label: z.string().nullable(), waiting_label: z.string().nullable(), workbook_url: z.string().nullable() }),
  connections: z.array(z.object({ system: z.enum(['jobber', 'quickbooks', 'gusto']), label: z.string(), status: z.string(), verified: z.boolean() })),
  recent: z.array(z.object({ id: z.string(), icon: z.enum(['check', 'workbook', 'clock']), text: z.string(), date_label: z.string() })),
  provenance: z.enum(['real', 'synthetic']),
})
export type IdleHome = z.infer<typeof IdleHome>

export function idleHomeFor(d: Data, declined: Set<string>): IdleHome | null {
  if (d.stopped || findPending(d, declined) || d.exceptions.some((e) => e.state !== 'resolved')) return null
  const candidate = (d.cycle as Data['cycle'] & { idle_home?: unknown }).idle_home
  const result = IdleHome.safeParse(candidate)
  if (!result.success) return null
  // Historical approval/submission claims require the existing verified state too.
  if (result.data.last.approved_label && d.cycle.stage1.state !== 'owner_approved') return null
  if (result.data.last.submitted_label && !['submitted_verified', 'paid_verified'].includes(d.cycle.destination)) return null
  return result.data
}

// A workbook path on disk or an external URL is never a browser download.
export function workbookDownloadUrl(value: string | null): string | null {
  if (!value?.startsWith('/api/') || value.startsWith('//') || /[\\\s]/.test(value)) return null
  const parsed = new URL(value, 'https://payrollpilot.invalid')
  return parsed.origin === 'https://payrollpilot.invalid' && parsed.pathname.startsWith('/api/') ? value : null
}
