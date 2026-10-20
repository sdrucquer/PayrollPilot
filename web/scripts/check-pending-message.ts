import assert from 'node:assert/strict'
import { pendingMessage } from '../src/pending-message'
import type { MessageBatch, PPEvent } from '../src/contracts'
const old = { id: 'old', state: 'draft', approval_id: null, created_at: '2026-10-20T13:58:11-07:00', text_hash: 'sha256:same', exception_ids: ['b', 'a'], intended_respondent_role: 'ops_lead', channel: 'imessage' } as MessageBatch & { created_at: string }
const latest = { ...old, id: 'latest', created_at: '2026-10-20T13:58:18-07:00', exception_ids: ['a', 'b'] }
const select = (b: MessageBatch[]) => pendingMessage(b, [], new Set())
assert.equal(select([old, latest, old])?.id, 'latest', 'global newest selection ignores duplicated thread references')
assert.equal(select([old, { ...latest, state: 'sent' }]), null, 'older identical unapproved draft does not resurface after send')
assert.equal(select([{ ...old, state: 'approved', approval_id: 'owner' }, { ...latest, state: 'sent' }])?.id, 'old', 'existing owner approval is never suppressed')
assert.equal(select([old, { ...latest, state: 'sent', text_hash: 'sha256:different' }])?.id, 'old')
assert.equal(select([old, { ...latest, state: 'sent', exception_ids: ['c'] }])?.id, 'old')
assert.equal(select([old, { ...latest, state: 'sent', intended_respondent_role: 'owner' }])?.id, 'old')
assert.equal(select([old, { ...latest, state: 'failed' }])?.id, 'old', 'a failed attempt does not suppress the old draft')
const unknown = { ...old, created_at: undefined }
assert.equal(select([unknown, { ...unknown, id: 'later', state: 'sent' }])?.id, 'old', 'unknown ordering never suppresses a draft')
const events = [{ type: 'message.drafted', at: '2026-10-20T14:00:00-07:00', refs: { batch_id: 'later' } }] as PPEvent[]
assert.equal(pendingMessage([unknown, { ...unknown, id: 'later' }], events, new Set())?.id, 'later')
assert.equal(select([old, { ...latest, declined_at: 'now' }])?.id, 'old')
assert.equal(old.state, 'draft'); assert.equal(old.approval_id, null)
console.log('Pending-message checks passed: newest, shared-thread dedupe, sent duplicate suppression, approval preservation, distinct scope/text/recipient, failed/unknown ordering and event fallback; no record changes.')
