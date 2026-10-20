import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { mkdir, readFile } from 'node:fs/promises'
import bundle from '../src/fixtures/bundle.ts'
import { idlePreview } from '../src/fixtures/idle-preview.ts'
const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PP_PLAYWRIGHT_MODULE ?? 'playwright')
const base = process.env.PP_QA_WEB ?? 'http://127.0.0.1:5174'
const browser = await chromium.launch({ executablePath: process.env.PP_CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 1180 }, reducedMotion: 'reduce' })
const errors = [], posts = []
page.on('pageerror', (e) => errors.push(e.message))
let mode = 'idle', failed = false
const cycle = { ...bundle.cycle, stage1: { ...bundle.cycle.stage1, state: 'owner_approved' }, destination: 'submitted_verified', idle_home: idlePreview }
const issue = { ...bundle.exceptions[0], state: 'resolved', message_ids: [] }
const batch = { id: 'idle-guard-message', cycle_id: cycle.id, exception_ids: [issue.id], intended_respondent_role: 'ops_lead', intended_respondent_label: 'Ops lead', actual_recipient_masked: '***-**12', channel: 'imessage', text: 'Which job was this shift on?', text_hash: 'sha256:reviewed-text', approval_id: null, state: 'draft', provider_message_id: null, sent_at: null, provider_status: null, provenance: 'synthetic' }
await page.route('**/api/**', async (route) => {
  const req = route.request(), path = new URL(req.url()).pathname
  if (req.method() !== 'GET') { posts.push(path); return route.fulfill({ status: 503, json: { error: 'preview_read_only' } }) }
  if (failed && path.endsWith('/readiness')) return route.fulfill({ status: 503, json: { error: 'qa_readiness_failure' } })
  let body
  if (path === `/api/cycles/${cycle.id}`) body = mode === 'missing' ? bundle.cycle : cycle
  else if (path.endsWith('/readiness')) body = bundle.readiness
  else if (path.endsWith('/exceptions')) body = ['message', 'correction'].includes(mode) ? [issue] : []
  else if (path.endsWith('/packet')) body = null
  else if (path === '/api/events') body = []
  else if (path === '/api/health') body = { ...bundle.health, adapters: { messaging: { mode: 'fake' } } }
  else if (path === `/api/exceptions/${issue.id}`) body = { ...issue, messages: { outbound: mode === 'message' ? [batch] : [], inbound: [] }, correction: mode === 'correction' ? { id: 'guard-correction', state: 'proposed' } : null }
  else if (path === '/api/corrections/guard-correction') body = { id: 'guard-correction', kind: 'job_allocation', before: { job_id: 'job_01' }, after: { job_id: 'job_02' }, calculation_impact: { stage1_wages_delta_cents: 0 }, state: 'proposed', target_version: 'sha256:server-version' }
  else return route.fulfill({ status: 404, json: { error: 'not_found' } })
  return route.fulfill({ json: body })
})
try {
  await page.goto(`${base}/preview/between-payrolls`)
  await page.getByRole('heading', { name: 'Next payroll starts Monday, Oct 26.' }).waitFor()
  assert.match(await page.locator('.i-preview').innerText(), /Synthetic scenario/)
  assert.ok(await page.getByRole('button', { name: 'Start early', exact: true }).isDisabled())
  assert.ok(await page.getByRole('button', { name: 'Change schedule', exact: true }).isDisabled())
  assert.ok(await page.getByRole('button', { name: 'Download workbook', exact: true }).isDisabled())
  assert.equal(await page.locator('.i-card').count(), 4)
  await mkdir('screenshots', { recursive: true })
  await page.screenshot({ path: 'screenshots/d05-idle-preview-1280.png', fullPage: true })
  if (process.env.PP_IDLE_REFERENCE_HTML) {
    const reference = await browser.newPage({ viewport: { width: 1280, height: 1180 }, reducedMotion: 'reduce' })
    await reference.setContent(await readFile(process.env.PP_IDLE_REFERENCE_HTML, 'utf8'))
    const target = page.locator('.i-page')
    const refRoot = reference.locator('[layer-name="Page"]')
    const actual = await target.screenshot(), expected = await refRoot.screenshot()
    const sharp = require(process.env.PP_SHARP_MODULE ?? 'sharp')
    const a = await sharp(actual).raw().toBuffer({ resolveWithObject: true })
    const b = await sharp(expected).raw().toBuffer({ resolveWithObject: true })
    console.log('Reference dimensions:', b.info.width, b.info.height, 'implementation:', a.info.width, a.info.height)
    assert.equal(a.info.width, b.info.width); assert.equal(a.info.height, b.info.height)
    let different = 0
    for (let i = 0; i < a.data.length; i += a.info.channels) {
      let delta = 0
      for (let c = 0; c < 3; c++) delta = Math.max(delta, Math.abs(a.data[i + c] - b.data[i + c]))
      if (delta > 20) different++
    }
    const ratio = different / (a.info.width * a.info.height)
    console.log(`ZIP visual difference (>20 per channel): ${(ratio * 100).toFixed(3)}%`)
    const bounds = await target.locator('.i-card').evaluateAll((els) => els.map((e) => { const r = e.getBoundingClientRect(); return [r.x, r.width, r.height] }))
    const refBounds = await reference.locator('[layer-name="Hero"], [layer-name="Last payroll"], [layer-name="Connections"], [layer-name="Activity"]').evaluateAll((els) => els.map((e) => { const r = e.getBoundingClientRect(); return [r.x, r.width, r.height] }))
    console.log('Card geometry actual/reference:', JSON.stringify(bounds), JSON.stringify(refBounds))
    assert.deepEqual(bounds, refBounds, 'all four reference card dimensions must match exactly')
    assert.ok(ratio < 0.01, 'desktop must visually match the supplied ZIP within 1%')
    await reference.close()
  }
  await page.setViewportSize({ width: 375, height: 900 })
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  await page.screenshot({ path: 'screenshots/d05-idle-preview-phone.png', fullPage: true })
  await page.getByRole('link', { name: 'Details', exact: true }).click()
  await page.getByRole('link', { name: 'Back to home' }).waitFor()
  await page.goto(base)
  await page.locator('.i-page').waitFor()
  assert.equal(await page.locator('.i-preview').count(), 0, 'explicit API payload selects idle at /')
  assert.match(await page.locator('.i-page').innerText(), /Scheduling controls are unavailable/)
  mode = 'message'; await page.reload()
  await page.getByRole('button', { name: 'Approve & send', exact: true }).waitFor()
  assert.equal(await page.locator('.i-page').count(), 0, 'resolved exception cannot hide an unsent batch')
  mode = 'correction'; await page.reload()
  await page.getByRole('button', { name: 'Approve & apply', exact: true }).waitFor()
  assert.equal(await page.locator('.i-page').count(), 0)
  mode = 'missing'; await page.reload(); await page.locator('.h-h1').waitFor()
  assert.equal(await page.locator('.i-page').count(), 0)
  mode = 'idle'; failed = true; await page.reload()
  await page.getByText(/Could not load payroll/).waitFor()
  assert.equal(await page.locator('.i-page').count(), 0, 'errors never become an idle success state')
  assert.deepEqual(posts, []); assert.deepEqual(errors, [])
  console.log('Idle browser checks passed: exact ZIP layout, mobile, read-only preview, explicit API activation, missing/error fallbacks, pending message/correction precedence and Details.')
} finally { await browser.close() }
