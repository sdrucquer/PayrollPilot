// npm run check:contracts
// 1. Validates the web fixture bundle against the zod mirrors in src/contracts.ts.
// 2. Validates any lane B fixtures in docs/contracts/fixtures/ whose shape we recognize.
// 3. Asserts the display invariants: null money is a dash, minutes format, handle masking, no "complete" rollup.
import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { z } from 'zod'
import * as C from '../src/contracts'
import { formatCents, formatMinutes, maskHandle } from '../src/format'
import { stage2Summary } from '../src/summary'

const here = dirname(fileURLToPath(import.meta.url))
let failures = 0
let checks = 0

function check(label: string, schema: z.ZodType, value: unknown) {
  checks++
  const r = schema.safeParse(value)
  if (!r.success) {
    failures++
    console.error(`FAIL ${label}`)
    for (const issue of r.error.issues.slice(0, 8)) console.error(`  ${issue.path.join('.')}: ${issue.message}`)
  } else console.log(`ok   ${label}`)
}
function assert(label: string, cond: boolean) {
  checks++
  if (!cond) { failures++; console.error(`FAIL ${label}`) } else console.log(`ok   ${label}`)
}

const bundlePath = join(here, '../src/fixtures/bundle.json')
const bundle = JSON.parse(readFileSync(bundlePath, 'utf8'))
check('bundle.health', C.Health, bundle.health)
check('bundle.cycle', C.PayrollCycle, bundle.cycle)
check('bundle.workers', z.array(C.Worker), bundle.workers)
check('bundle.readiness', C.ReadinessResponse, bundle.readiness)
check('bundle.readiness_after_t02', C.ReadinessResponse, bundle.readiness_after_t02)
check('bundle.exceptions', z.array(C.PayrollException), bundle.exceptions)
check('bundle.events', z.array(C.PPEvent), bundle.events)

// Lane B fixtures (shapes per CONTRACTS section 6). Validate the parts that are contract records.
for (const fxDir of [join(here, '../../docs/contracts/fixtures'), join(here, '../src/fixtures/laneb')]) {
if (existsSync(fxDir)) {
  for (const f of readdirSync(fxDir).filter((n) => n.endsWith('.json'))) {
    const data = JSON.parse(readFileSync(join(fxDir, f), 'utf8'))
    if (data && typeof data === 'object' && 'cycle' in data) check(`${fxDir.split('/').slice(-2).join('/')}/${f}: cycle`, C.PayrollCycle, data.cycle)
    if (data && typeof data === 'object' && 'workers' in data) check(`${f}: workers`, z.array(C.Worker), data.workers)
    if (data && typeof data === 'object' && 'exceptions' in data && Array.isArray(data.exceptions)
        && data.exceptions[0]) check(`${f}: exceptions (expected subset)`, z.array(C.PayrollException.pick({
          id: true, category: true, entity_refs: true, stage_impact: true, intended_respondent_role: true, title: true,
        })), data.exceptions)
    if (!('cycle' in data) && !('workers' in data) && !('exceptions' in data)) console.log(`skip ${f} (no recognized contract record at top level)`)
  }
} else console.log(`skip ${fxDir} (not present yet)`)
}

assert('formatCents(null) is a dash', formatCents(null) === '—')
assert('formatCents(0) is $0.00, not a dash', formatCents(0) === '$0.00')
assert('formatCents(480000) is $4,800.00', formatCents(480000) === '$4,800.00')
assert('formatCents(-2550) is -$25.50', formatCents(-2550) === '-$25.50')
assert('formatMinutes(134) is 2h 14m', formatMinutes(134) === '2h 14m')
assert('formatMinutes(null) is a dash', formatMinutes(null) === '—')
assert('maskHandle hides all but last 2', maskHandle('test-handle-ab12') === '***-**12')
const summary = stage2Summary(bundle.readiness.items)
console.log(`     stage2 summary: ${summary}`)
assert('stage2 summary never says "complete"', !/complete/i.test(summary))
assert('stage2 summary lists items separately', summary.split(';').length >= 2)

console.log(`\n${checks - failures}/${checks} checks passed`)
process.exit(failures ? 1 : 0)
