import assert from 'node:assert/strict'
import bundle from '../src/fixtures/bundle'
import { idlePreview } from '../src/fixtures/idle-preview'
import { IdleHome, idleHomeFor, workbookDownloadUrl } from '../src/idle-state'
import type { Data } from '../src/home-state'
const data = (): Data => ({ cycle: structuredClone(bundle.cycle), readiness: structuredClone(bundle.readiness), exceptions: [], events: [], packet: null, threads: [], stopped: false })
let d = data()
assert.equal(idleHomeFor(d, new Set()), null, 'missing idle metadata is active home')
const home = structuredClone(idlePreview)
home.last.approved_label = null; home.last.submitted_label = null
Object.assign(d.cycle, { idle_home: home })
assert.equal(idleHomeFor(d, new Set())?.state, 'between_payrolls')
d.stopped = true
assert.equal(idleHomeFor(d, new Set()), null, 'a paused run is not between payrolls')
d.stopped = false
d.exceptions = [{ ...bundle.exceptions[0], state: 'needs_approval' }]
assert.equal(idleHomeFor(d, new Set()), null, 'open owner work is never hidden')
d.exceptions = []
d.threads = [{ batches: [{ id: 'pending', state: 'draft', exception_ids: [] }], inbound: [] }] as unknown as Data['threads']
assert.equal(idleHomeFor(d, new Set()), null, 'pending exact text takes precedence')
d.threads = [{ batches: [], inbound: [], correction: { id: 'pending', state: 'proposed' } }] as unknown as Data['threads']
assert.equal(idleHomeFor(d, new Set()), null, 'pending correction takes precedence')
d.threads = []
Object.assign(d.cycle, { idle_home: idlePreview })
assert.equal(idleHomeFor(d, new Set()), null, 'unverified approval/submission badges are refused')
d.cycle.stage1.state = 'owner_approved'; d.cycle.destination = 'submitted_verified'
assert.ok(idleHomeFor(d, new Set()))
assert.equal(IdleHome.safeParse({ ...home, next: { ...home.next, days_until_start: -1 } }).success, false)
assert.equal(workbookDownloadUrl('/api/workbooks/example/download'), '/api/workbooks/example/download')
for (const url of ['https://elsewhere.example/file', '//elsewhere.example/file', 'javascript:alert(1)', '/private/file.xlsx', '/api/../private/file.xlsx', '/api/\\elsewhere/file']) assert.equal(workbookDownloadUrl(url), null)
console.log('Idle state checks passed: explicit payload, all approval precedence, paused/open-work guards, historical verification, countdown validation and safe workbook URLs.')
