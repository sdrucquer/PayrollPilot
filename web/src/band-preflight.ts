import type { MessageBatch } from './contracts'

export interface BandPreflightIO {
  getCase: (id: string) => Promise<{ owner_agent?: string }>
  handoff: (id: string) => Promise<unknown>
  getBatch: (batch: MessageBatch) => Promise<MessageBatch | undefined>
}

export async function ensureResolutionHandoffs(ids: string[], io: BandPreflightIO): Promise<void> {
  for (const id of new Set(ids)) {
    const current = await io.getCase(id)
    if (current.owner_agent === 'resolution') continue
    await io.handoff(id)
    const persisted = await io.getCase(id)
    if (persisted.owner_agent !== 'resolution') throw new Error('Band handoff did not establish Resolution ownership. Nothing was drafted or sent.')
  }
}

export async function preflightNewMessage(batch: MessageBatch, io: BandPreflightIO): Promise<void> {
  // Existing owner approvals and sent batches keep their existing flow.
  if (batch.state !== 'draft' || batch.approval_id) return
  const current = await io.getBatch(batch)
  if (!current) throw new Error('The message draft is no longer available. Refresh before approving.')
  if (current.state !== 'draft' || current.approval_id) return
  await ensureResolutionHandoffs(current.exception_ids, io)
}
