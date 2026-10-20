// The only module that knows whether data comes from fixtures or the live /api.
import bundle from './fixtures/bundle'
import {
  type ExceptionDetail, type Health, type PayrollCycle, type PayrollException, type PPEvent,
  type ReadinessResponse, type Worker,
} from './contracts'

export type DataMode = 'fixture' | 'api'
export const DATA_MODE: DataMode = import.meta.env.VITE_DATA_MODE === 'api' ? 'api' : 'fixture'

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
const clone = <T>(v: T): T => structuredClone(v)

export const api = {
  mode: DATA_MODE,

  health: (): Promise<Health> => (DATA_MODE === 'fixture' ? Promise.resolve(clone(bundle.health)) : http('/health')),

  // In api mode the board needs a cycle id; the lead's flow loads the fixture first.
  loadCycle: (source: 'fixture' | 'private_snapshot', name: string): Promise<PayrollCycle> =>
    DATA_MODE === 'fixture' ? Promise.resolve(clone(bundle.cycle)) : post('/cycles/load', { source, name }),

  cycle: (id: string): Promise<PayrollCycle> =>
    DATA_MODE === 'fixture' ? Promise.resolve(clone(bundle.cycle)) : http(`/cycles/${id}`),

  readiness: (id: string): Promise<ReadinessResponse> =>
    DATA_MODE === 'fixture' ? Promise.resolve(clone(bundle.readiness)) : http(`/cycles/${id}/readiness`),

  exceptions: (id: string): Promise<PayrollException[]> =>
    DATA_MODE === 'fixture' ? Promise.resolve(clone(bundle.exceptions)) : http(`/cycles/${id}/exceptions`),

  exception: (id: string): Promise<ExceptionDetail> => {
    if (DATA_MODE === 'api') return http(`/exceptions/${id}`)
    const e = bundle.exceptions.find((x) => x.id === id)
    return e ? Promise.resolve(clone(e)) : Promise.reject(new ApiError(404, `exception ${id} not in fixture`))
  },

  events: (cycleId: string): Promise<PPEvent[]> =>
    DATA_MODE === 'fixture'
      ? Promise.resolve(clone(bundle.events))
      : http(`/events?cycle_id=${encodeURIComponent(cycleId)}`),

  // No workers route exists in CONTRACTS section 5. Fixture mode has them; api mode falls back to the packet.
  workers: async (cycleId: string): Promise<Worker[]> => {
    if (DATA_MODE === 'fixture') return clone(bundle.workers)
    try {
      const packet = await http<{ identities?: Worker[]; workers?: Worker[] }>(`/cycles/${cycleId}/packet`)
      return packet.identities ?? packet.workers ?? []
    } catch {
      return []
    }
  },
}

export const DEFAULT_CYCLE_ID = import.meta.env.VITE_CYCLE_ID ?? bundle.cycle.id
