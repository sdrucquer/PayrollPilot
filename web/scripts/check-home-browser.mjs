// Uses an isolated API with FakeMessaging. Refuses to run against a real bridge.
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { mkdir } from 'node:fs/promises'
const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PP_PLAYWRIGHT_MODULE ?? 'playwright')
const base = process.env.PP_QA_API ?? 'http://127.0.0.1:18000'
const web = process.env.PP_QA_WEB ?? 'http://127.0.0.1:5174'
async function api(path, body, headers = {}) {
  const r = await fetch(`${base}/api${path}`, body === undefined ? undefined : { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(body) })
  assert.ok(r.ok, `${path}: HTTP ${r.status}`)
  return r.json()
}
assert.equal((await api('/health')).adapters.messaging.mode, 'fake', 'QA must never send real texts')
const cycle = await api('/cycles/load', { source: 'fixture', name: 'cycle_synthetic_v1' })
const { exceptions } = await api(`/cycles/${cycle.id}/audit`, {})
const issue = exceptions.find((e) => e.category === 'missing_job')
assert.ok(issue)
for (const e of exceptions) {
  const detail = await api(`/exceptions/${e.id}`)
  for (const b of detail.messages.outbound) if (['draft', 'approved'].includes(b.state) && !b.declined_at) await api(`/messages/${b.id}/decline`, { target_version: b.text_hash })
}
let batch = await api('/messages/draft', { exception_ids: [issue.id] })
const browser = await chromium.launch({ executablePath: process.env.PP_CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
const page = await browser.newPage({ viewport: { width: 1280, height: 1100 }, reducedMotion: 'reduce', deviceScaleFactor: 2 })
const errors = [], effects = []
let failEvents = false, readyView = false
page.on('pageerror', (e) => errors.push(e.message))
await page.route('**/api/**', async (route) => {
  const req = route.request(), url = new URL(req.url())
  if (req.method() === 'POST') effects.push({ path: url.pathname, body: req.postDataJSON() })
  if (failEvents && url.pathname === '/api/events') return route.fulfill({ status: 503, json: { error: 'qa_event_outage' } })
  const response = await route.fetch({ url: `${base}${url.pathname}${url.search}` })
  if (readyView && req.method() === 'GET') {
    const body = await response.json()
    if (url.pathname === `/api/cycles/${cycle.id}`) {
      body.stage1.state = 'review_ready'; body.stage2.state = 'review_ready'
      return route.fulfill({ response, json: body })
    }
    if (url.pathname.endsWith('/readiness')) {
      body.stage1.state = 'ready'; body.stage1.blockers = []
      return route.fulfill({ response, json: body })
    }
    if (url.pathname.endsWith('/exceptions')) return route.fulfill({ response, json: [] })
  }
  return route.fulfill({ response })
})
try {
  await page.goto(web)
  await page.getByRole('button', { name: 'Approve & send', exact: true }).waitFor()
  assert.equal(await page.locator('.h-approve').count(), 1)
  assert.equal(await page.locator('.h-steps .s').count(), 6)
  assert.equal(await page.locator('.h-steps .div').count(), 1)
  assert.match(await page.locator('.h-contact').innerText(), /\*|•/)
  assert.match(await page.locator('body').innerText(), /Fake messaging/)
  assert.equal(await page.locator('.h-bubble').innerText(), batch.text)
  await mkdir('screenshots', { recursive: true })
  await page.screenshot({ path: 'screenshots/d04-home-api-1280.png', fullPage: true })
  await page.getByRole('button', { name: 'Edit', exact: true }).click()
  const edited = `${batch.text}\nThanks for checking.`
  await page.getByRole('textbox', { name: 'Edit message text' }).fill(edited)
  await page.getByRole('button', { name: 'Save new version' }).click()
  await page.getByText(edited, { exact: true }).waitFor()
  batch = (await api(`/exceptions/${issue.id}`)).messages.outbound.find((b) => b.id === batch.id)
  assert.equal(batch.text, edited)
  assert.equal(batch.approval_id, null)
  await page.getByRole('button', { name: 'Approve & send', exact: true }).click()
  await page.locator('.h-toast').filter({ hasText: 'Sent to the Ops lead.' }).waitFor()
  const approval = effects.find((e) => e.path === '/api/approvals')
  assert.equal(approval.body.kind, 'message_send')
  assert.equal(approval.body.target_version, batch.text_hash)
  assert.ok(effects.findIndex((e) => e.path === '/api/approvals') < effects.findIndex((e) => e.path.endsWith('/send')))
  await api('/inbound', { provider_message_id: `d04-${Date.now()}`, correlated_batch_id: batch.id, raw_text: 'That shift was Job 02.', provenance: 'test_reply' }, { 'X-PP-Bridge-Token': process.env.PP_QA_BRIDGE_TOKEN ?? 'change-me' })
  const detail = await api(`/exceptions/${issue.id}`)
  assert.ok(detail.resolution, 'synthetic reply should produce a resolution')
  const correction = await api('/corrections', { resolution_id: detail.resolution.id, kind: 'job_allocation', after: { time_entry_id: issue.entity_refs.time_entry_ids[0], job_id: 'job_02' } })
  await page.reload()
  await page.getByRole('button', { name: 'Approve & apply', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Approve & apply', exact: true }).click()
  await page.locator('.h-toast').filter({ hasText: 'Correction applied. Payroll recalculated.' }).waitFor()
  const ca = effects.find((e) => e.path === '/api/approvals' && e.body.kind === 'local_correction')
  assert.equal(ca.body.target_version, correction.target_version)
  assert.equal((await api(`/corrections/${correction.id}`)).state, 'applied')
  const next = exceptions.find((e) => e.category === 'long_shift')
  const declined = await api('/messages/draft', { exception_ids: [next.id] })
  await page.reload()
  await page.getByRole('button', { name: 'Decline', exact: true }).click()
  await page.locator('.h-toast').filter({ hasText: 'Declined. Nothing was sent.' }).waitFor()
  await page.reload()
  await page.locator('.h-h1').waitFor()
  assert.equal(await page.getByRole('button', { name: 'Approve & send', exact: true }).count(), 0)
  assert.ok((await api(`/exceptions/${next.id}`)).messages.outbound.find((b) => b.id === declined.id).declined_at)
  await page.getByRole('button', { name: 'Pause', exact: true }).click()
  await page.getByRole('button', { name: 'Resume', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Resume', exact: true }).click()
  await page.getByRole('button', { name: 'Pause', exact: true }).waitFor()
  failEvents = true
  await page.getByRole('alert').filter({ hasText: 'Payroll could not refresh' }).waitFor({ timeout: 10000 })
  assert.equal(await page.getByRole('button', { name: 'Pause', exact: true }).isDisabled(), true)
  failEvents = false
  await page.getByRole('alert').filter({ hasText: 'Payroll could not refresh' }).waitFor({ state: 'hidden', timeout: 10000 })
  await page.setViewportSize({ width: 375, height: 900 })
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'no phone horizontal overflow')
  await page.screenshot({ path: 'screenshots/d04-home-api-phone.png', fullPage: true })
  // Presentation-only ready state: explicit API-shaped stage states, unchanged numbers.
  readyView = true
  await page.reload()
  await page.getByText('Pilot has a draft for you', { exact: true }).waitFor()
  assert.equal(await page.locator('.h-approve').count(), 1)
  assert.equal(await page.locator('.h-steps .done').count(), 6)
  assert.equal(await page.locator('.h-tiles .h-tile').count(), 3)
  assert.ok(await page.getByRole('button', { name: 'Draft approval unavailable' }).isDisabled())
  await page.screenshot({ path: 'screenshots/d04-ready-api-phone.png', fullPage: true })
  await page.getByRole('link', { name: 'Details', exact: true }).first().click()
  await page.getByRole('link', { name: 'Back to home' }).waitFor()
  assert.deepEqual(errors, [])
  console.log('Browser QA passed: exact preview, masked recipient, Edit, versioned Approve/Send and Approve/Apply, persistent Decline, Pause/Resume, error recovery, 375px layout, six-step ready view and Details.')
} catch (e) { console.error('Visible action error:', await page.locator('.h-err').allTextContents()); await page.screenshot({ path: 'screenshots/d04-qa-failure.png', fullPage: true }); throw e } finally { await browser.close() }
