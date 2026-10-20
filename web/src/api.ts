// The only module that knows whether data comes from fixtures (plus sim.ts) or the live /api.
import bundle from './fixtures/bundle'
import { sim } from './sim'
import type {
  Approval, Health, InboundMessage, LocalCorrection, MessageBatch, ParsedReply, PayrollCycle, PayrollException,
  PPEvent, ReadinessResponse, Resolution, Worker,
} from './contracts'

export type DataMode = 'fixture' | 'api'
export const DATA_MODE: DataMode = import.meta.env.VITE_DATA_MODE === 'api' ? 'api' : 'fixture'
const FX = DATA_MODE === 'fixture'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    let detail = res.statusText
    try { detail = JSON.stringify(await res.json()) } catch { /* body not JSON */ }
    throw new ApiError(res.status, `${init?.method ?? 'GET'} /api${path} failed (${res.status}): ${detail}`)
  }
  return (await res.json()) as T
}
const post = <T>(path: string, body: unknown) => http<T>(path, { method: 'POST', body: JSON.stringify(body) })
const ok = <T>(fn: () => T): Promise<T> => { try { return Promise.resolve(fn()) } catch (e) { return Promise.reject(e) } }

export interface Thread {
  exception: PayrollException
  batches: MessageBatch[]
  inbound: InboundMessage[]
  parsed: ParsedReply[]
  resolution: Resolution | null
  correction: LocalCorrection | null
  approvals: Approval[]
  blockedInboundIds: string[]
}

// GET /api/exceptions/{id} returns Exception + messages + resolution + correction. "messages" is not
// pinned in CONTRACTS, so accept batches and inbound mixed in one array, plus optional parsed/approvals.
type Detail = PayrollException & {
  messages?: Record<string, unknown>[] | { outbound?: MessageBatch[]; inbound?: InboundMessage[] }
  batches?: MessageBatch[]; inbound?: InboundMessage[]
  parsed?: ParsedReply[]; parsed_replies?: ParsedReply[]; approvals?: Approval[]
  resolution?: Resolution | null; correction?: LocalCorrection | null
}
function normalize(d: Detail, events: PPEvent[]): Thread {
  // Backend (A-02) returns messages: {outbound: [MessageBatch], inbound: [InboundMessage]}.
  const m = d.messages
  const msgs: Record<string, unknown>[] = Array.isArray(m) ? m : []
  const obj = m && !Array.isArray(m) ? m : undefined
  const batches = d.batches ?? obj?.outbound ?? (msgs.filter((x) => 'text_hash' in x) as unknown as MessageBatch[])
  const inbound = d.inbound ?? obj?.inbound ?? (msgs.filter((x) => 'raw_text' in x) as unknown as InboundMessage[])
  for (const i of inbound as (InboundMessage & { parsed?: ParsedReply })[]) if (i.parsed) msgs.push({ parsed: i.parsed })
  const nested = msgs.map((m) => m.parsed).filter(Boolean) as ParsedReply[]
  const parsed = d.parsed ?? d.parsed_replies ?? nested
  const blockedInboundIds = events.filter((e) => e.type === 'blocked.unauthorized_instruction')
    .flatMap((e) => Object.values(e.refs).map(String))
  const { messages: _m, batches: _b, inbound: _i, parsed: _p, parsed_replies: _pr, approvals, resolution, correction, ...exception } = d
  void _m; void _b; void _i; void _p; void _pr
  return { exception, batches, inbound, parsed, resolution: resolution ?? null, correction: correction ?? null, approvals: approvals ?? [], blockedInboundIds }
}

export const api = {
  mode: DATA_MODE,

  health: (): Promise<Health> => (FX ? ok(() => structuredClone(bundle.health)) : http('/health')),
  loadCycle: (source: 'fixture' | 'private_snapshot', name: string): Promise<PayrollCycle> =>
    FX ? ok(() => structuredClone(bundle.cycle)) : post('/cycles/load', { source, name }),
  cycle: (id: string): Promise<PayrollCycle> => (FX ? ok(() => structuredClone(bundle.cycle)) : http(`/cycles/${id}`)),
  readiness: (id: string): Promise<ReadinessResponse> => (FX ? ok(sim.readiness) : http(`/cycles/${id}/readiness`)),
  exceptions: (id: string): Promise<PayrollException[]> => (FX ? ok(sim.exceptions) : http(`/cycles/${id}/exceptions`)),
  events: (cycleId: string): Promise<PPEvent[]> =>
    FX ? ok(sim.events) : http(`/events?cycle_id=${encodeURIComponent(cycleId)}`),

  thread: async (id: string, cycleId: string): Promise<Thread> => {
    if (FX) return sim.thread(id)
    const [d, ev] = await Promise.all([http<Detail>(`/exceptions/${id}`), api.events(cycleId).catch(() => [] as PPEvent[])])
    return normalize(d, ev)
  },

  // No workers route exists in CONTRACTS section 5. Fixture mode has them; api mode falls back to the packet.
  workers: async (cycleId: string): Promise<Worker[]> => {
    if (FX) return structuredClone(bundle.workers)
    try {
      const packet = await http<{ identities?: Worker[]; workers?: Worker[] }>(`/cycles/${cycleId}/packet`)
      return packet.identities ?? packet.workers ?? []
    } catch {
      return []
    }
  },

  // Actions (CONTRACTS section 5).
  draft: (exception_ids: string[]): Promise<MessageBatch> => (FX ? sim.draft(exception_ids) : post('/messages/draft', { exception_ids })),
  editDraft: (batchId: string, text: string): Promise<void> => {
    if (FX) return sim.editDraft(batchId, text)
    return Promise.reject(new ApiError(501, 'Editing a draft is not an API route in CONTRACTS v1.1'))
  },
  approve: (body: { kind: Approval['kind']; target_id: string; target_version: string; scope_text: string }): Promise<Approval> =>
    FX ? ok(() => sim.approve(body)) : post('/approvals', body),
  send: (batchId: string): Promise<MessageBatch> => (FX ? ok(() => sim.send(batchId)) : post(`/messages/${batchId}/send`, {})),
  clarify: (exceptionId: string): Promise<MessageBatch> =>
    FX ? sim.draft([exceptionId], true) : post(`/exceptions/${exceptionId}/clarify`, {}),
  proposeCorrection: (resolution_id: string, kind: LocalCorrection['kind'], after: Record<string, unknown>): Promise<LocalCorrection> =>
    FX ? ok(() => sim.proposeCorrection(resolution_id, kind, after)) : post('/corrections', { resolution_id, kind, after }),
  applyCorrection: (id: string): Promise<unknown> => (FX ? ok(() => sim.applyCorrection(id)) : post(`/corrections/${id}/apply`, {})),
  handoff: (exceptionId: string): Promise<unknown> =>
    FX ? Promise.reject(new ApiError(501, 'Handoff needs the live API')) : post(`/exceptions/${exceptionId}/handoff`, {}),
  // Fixture only: replays the scripted lane B test reply for a sent batch.
  simulateReply: (batchId: string): Promise<void> =>
    FX ? ok(() => sim.simulateReply(batchId)) : Promise.reject(new ApiError(400, 'Replies arrive from the bridge in api mode')),
}

export const DEFAULT_CYCLE_ID = import.meta.env.VITE_CYCLE_ID ?? bundle.cycle.id
