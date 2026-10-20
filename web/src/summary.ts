import type { CompKind, CompensationItem } from './contracts'
import { humanize } from './format'

export const STAGE2: { kind: CompKind; title: string }[] = [
  { kind: 'quote_commission', title: 'Quote commission' },
  { kind: 'marketing', title: 'Marketing' },
  { kind: 'tip', title: 'Tips' },
  { kind: 'manager_pool', title: 'Manager pool' },
]

const KIND_LABEL: Record<CompKind, string> = {
  wages: 'wages', quote_commission: 'quote commission', marketing: 'marketing', tip: 'tip', manager_pool: 'manager pool',
}

// Lists each Stage 2 item separately by readiness state. Never rolls up to a single "done" word.
export function stage2Summary(items: CompensationItem[]): string {
  const parts: string[] = []
  for (const { kind } of STAGE2) {
    const byState = new Map<string, number>()
    for (const i of items.filter((x) => x.kind === kind)) byState.set(i.readiness.state, (byState.get(i.readiness.state) ?? 0) + 1)
    for (const [state, n] of byState) parts.push(`${n} ${KIND_LABEL[kind]} ${humanize(state)}`)
  }
  return parts.length ? parts.join('; ') : 'No Stage 2 items reported'
}
