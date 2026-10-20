import type { MessageBatch, PPEvent } from './contracts'

// Display selection only. Records, approvals and delivery state are never changed.
export function pendingMessage(batches: MessageBatch[], events: PPEvent[], declined: ReadonlySet<string>): MessageBatch | null {
  const declinedOnServer = (b: MessageBatch) => !!(b as MessageBatch & { declined_at?: string | null }).declined_at
  const unique = [...new Map(batches.map((b) => [b.id, b])).values()]
  const drafts = new Map<string, { time: number; order: number }>()
  events.forEach((e, order) => {
    if (e.type === 'message.drafted' && typeof e.refs.batch_id === 'string') drafts.set(e.refs.batch_id, { time: Date.parse(e.at) || 0, order })
  })
  const rank = (b: MessageBatch) => ({ time: Date.parse((b as MessageBatch & { created_at?: string }).created_at ?? '') || drafts.get(b.id)?.time || 0, order: drafts.get(b.id)?.order ?? -1 })
  const compare = (a: MessageBatch, b: MessageBatch) => rank(b).time - rank(a).time || rank(b).order - rank(a).order
  const newer = (a: MessageBatch, b: MessageBatch) => rank(a).time > rank(b).time || (rank(a).time > 0 && rank(a).time === rank(b).time && rank(a).order > rank(b).order)
  const sameQuestion = (a: MessageBatch, b: MessageBatch) => a.text_hash === b.text_hash && a.intended_respondent_role === b.intended_respondent_role && a.channel === b.channel && [...new Set(a.exception_ids)].sort().join('\u0000') === [...new Set(b.exception_ids)].sort().join('\u0000')
  return unique.sort(compare).find((b) => {
    if (!['draft', 'approved'].includes(b.state) || declinedOnServer(b) || declined.has(b.id)) return false
    if (b.state === 'draft' && !b.approval_id && unique.some((other) => other.id !== b.id && !declinedOnServer(other) && ['draft', 'approved', 'sent', 'delivered'].includes(other.state) && newer(other, b) && sameQuestion(other, b))) return false
    return true
  }) ?? null
}
