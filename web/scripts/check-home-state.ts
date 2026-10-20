import assert from 'node:assert/strict'
import { maskText } from '../src/format'
import bundle from '../src/fixtures/bundle'
import { activity, findPending, steps, wagesLine, stage2Line, type Data } from '../src/home-state'

const data = (): Data => ({ cycle: structuredClone(bundle.cycle), readiness: structuredClone(bundle.readiness), exceptions: [], events: [], packet: null, threads: [], stopped: false })
let d = data()
assert.equal(steps(d, null).doneCount, 0, 'a loaded cycle alone is not a gathered snapshot')
d.cycle.stage1.state = 'resolving'
assert.deepEqual(steps(d, null).done, [true, true, false, false, false, false], 'stage states advance the first two steps')
d.readiness.stage1 = { ...d.readiness.stage1, state: 'ready', blockers: [] }
d.cycle.stage1.state = 'review_ready'
assert.equal(steps(d, null).doneCount, 4, 'stage 2 is distinct from wage readiness')
d.cycle.stage2.state = 'review_ready'
assert.equal(steps(d, null).doneCount, 6, 'the ready screen can reach all six steps')
assert.equal(steps(d, null).cur, -1)
assert.equal(steps(d, null).ready, true)
d.readiness.stage1.state = 'blocked'
assert.equal(steps(d, null).ready, false, 'stale stage state cannot override blocked wages')
d.readiness.workers = { a: { ...d.readiness.stage1, state: 'ready' }, b: { ...d.readiness.stage1, state: 'blocked' } }
assert.match(wagesLine(d).text, /1 of 2 workers/, 'readiness API drives worker counts without the optional packet')
assert.equal(stage2Line([]).ok, false, 'absent items cannot claim readiness')
const b = { id: 'batch', state: 'draft', text_hash: 'sha256:test', exception_ids: [] }
d.threads = [{ batches: [{ ...b, declined_at: '2026-10-20T13:00:00-07:00' }] }] as Data['threads']
assert.equal(findPending(d, new Set()), null, 'persisted declines stay out of the approval card')
d.threads = [{ batches: [b], inbound: [] }] as Data['threads']
const pending = findPending(d, new Set())
assert.equal(pending?.kind, 'message')
assert.equal(steps(d, pending).ready, false)
d.events = [
  { id: 'new', at: '2026-10-20T13:02:00-07:00', type: 'clarification.needed', refs: {} },
  { id: 'old', at: '2026-10-20T13:01:00-07:00', type: 'message.received', refs: {} },
] as Data['events']
assert.equal(activity(d)[0].id, 'new', 'activity sorts by event time')
assert.equal(activity(d)[0].text, 'The reply needs clarification', 'clarification needed does not claim a draft exists')
assert.equal(activity(d)[1].test, false, 'real replies do not receive invented test provenance')
console.log('Home state checks passed: stage progression, readiness, pending approval, persistent decline, event ordering and honest copy')

assert.equal(maskText('Shift on 2026-09-29 (2h14m)'), 'Shift on 2026-09-29 (2h14m)')
assert.equal(maskText('Call +1 (555) 000-0012'), 'Call ***-**12')
