import assert from 'node:assert/strict'
import { ensureResolutionHandoffs, preflightNewMessage, type BandPreflightIO } from '../src/band-preflight'
import type { MessageBatch } from '../src/contracts'
let calls: string[] = [], ownership: Record<string, string> = { a: 'audit', b: 'resolution' }
const io: BandPreflightIO = {
  getCase: async (id) => { calls.push(`get:${id}`); return { owner_agent: ownership[id] } },
  handoff: async (id) => { calls.push(`handoff:${id}`); ownership[id] = 'resolution' },
  getBatch: async (b) => { calls.push('batch'); return b },
}
await ensureResolutionHandoffs(['a', 'a', 'b'], io)
assert.deepEqual(calls, ['get:a', 'handoff:a', 'get:a', 'get:b'])
calls = []; ownership = { a: 'audit', b: 'audit' }
await assert.rejects(ensureResolutionHandoffs(['a', 'b'], { ...io, handoff: async () => { throw new Error('Band unavailable') } }), /Band unavailable/)
assert.deepEqual(calls, ['get:a'], 'failed handoff stops all later work')
await assert.rejects(ensureResolutionHandoffs(['a'], { ...io, handoff: async () => {} }), /did not establish/, '200 without persisted ownership is not success')
const batch = { id: 'batch', state: 'draft', approval_id: null, exception_ids: ['a'] } as MessageBatch
calls = []; ownership.a = 'audit'
await preflightNewMessage(batch, io)
assert.deepEqual(calls, ['batch', 'get:a', 'handoff:a', 'get:a'])
for (const state of ['approved', 'sent', 'delivered'] as const) {
  calls = []; await preflightNewMessage({ ...batch, state }, io); assert.deepEqual(calls, [])
}
calls = []; await preflightNewMessage({ ...batch, approval_id: 'existing' }, io); assert.deepEqual(calls, [])
calls = []; await preflightNewMessage(batch, { ...io, getBatch: async () => ({ ...batch, state: 'approved', approval_id: 'owner' }) }); assert.deepEqual(calls, [])
await assert.rejects(preflightNewMessage(batch, { ...io, getBatch: async () => undefined }), /no longer available/)
console.log('Band preflight checks passed: persisted ownership, dedupe, sequential failure, no false 200 success, new-send gate and existing approval/sent preservation.')
