// Fixture-mode simulation of the backend flow (FakeMessaging-like). Used only when VITE_DATA_MODE=fixture.
// Everything it produces is labeled: provider_status says "fixture simulation", replies are test_reply,
// and the UI shows a "Fixture simulation" banner. It never computes money: correction impacts come
// verbatim from lane B's readiness_matrix_v1.json, otherwise they are left empty.
import bundle from './fixtures/bundle'
import matrix from './fixtures/laneb/readiness_matrix_v1.json'
import type {
  Approval, InboundMessage, LocalCorrection, MessageBatch, ParsedReply, PayrollException, PPEvent,
  ReadinessResponse, Resolution,
} from './contracts'

type Status = ParsedReply['answers'][number]['status']
const clone = <T>(v: T): T => structuredClone(v)
const now = () => new Date().toISOString()
let seq = 0
const nid = (p: string) => `${p}${Date.now().toString(36)}${(seq++).toString(36)}`

export async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return 'sha256:' + [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

const T02 = (matrix as unknown as { after_t02_correction: { correction: Pick<LocalCorrection, 'kind' | 'before' | 'after' | 'calculation_impact'> } })
  .after_t02_correction.correction

const S = {
  exceptions: clone(bundle.exceptions) as PayrollException[],
  readiness: clone(bundle.readiness) as ReadinessResponse,
  events: clone(bundle.events) as PPEvent[],
  batches: [] as MessageBatch[],
  inbound: [] as InboundMessage[],
  parsed: [] as ParsedReply[],
  resolutions: [] as Resolution[],
  corrections: [] as LocalCorrection[],
  approvals: [] as Approval[],
  blocked: new Set<string>(),
  usedReplies: new Set<string>(),
}
const cycleId = bundle.cycle.id

function emit(actor: PPEvent['actor'], type: PPEvent['type'], summary: string, refs: Record<string, unknown> = {}) {
  S.events.push({ id: nid('evt_sim_'), at: now(), cycle_id: cycleId, actor, type, summary, refs, usage: null, duration_ms: null })
}
function exc(id: string): PayrollException {
  const e = S.exceptions.find((x) => x.id === id)
  if (!e) throw new Error(`exception ${id} not in fixture`)
  return e
}
function setState(e: PayrollException, state: PayrollException['state'], next: string) {
  if (e.state !== state) emit('system', 'exception.state_changed', `${e.id}: ${e.state} -> ${state}`, { exception_id: e.id })
  e.state = state
  e.next_action = next
  e.updated_at = now()
}

export const sim = {
  exceptions: () => clone(S.exceptions),
  readiness: () => clone(S.readiness),
  events: () => clone(S.events),
  thread(id: string) {
    const e = exc(id)
    const batches = S.batches.filter((b) => b.exception_ids.includes(id))
    const inbound = S.inbound.filter((m) => batches.some((b) => b.id === m.correlated_batch_id))
    const parsed = S.parsed.filter((p) => inbound.some((m) => m.id === p.inbound_id))
    const resolution = S.resolutions.find((r) => r.exception_id === id) ?? null
    const correction = resolution ? S.corrections.find((c) => c.resolution_id === resolution.id) ?? null : null
    const approvals = S.approvals.filter((a) => batches.some((b) => b.id === a.target_id) || a.target_id === correction?.id)
    return clone({ exception: e, batches, inbound, parsed, resolution, correction, approvals, blockedInboundIds: [...S.blocked] })
  },

  async draft(exceptionIds: string[], followUp = false): Promise<MessageBatch> {
    const list = exceptionIds.map(exc)
    const role = list[0].intended_respondent_role
    const qs = list.map((e, i) => `(${i + 1}) ${e.title}${followUp ? ' Can you confirm exactly which job or value is right?' : '?'}`)
    const text = `${followUp ? 'Quick follow-up on payroll' : `Hi, ${list.length} quick payroll check${list.length > 1 ? 's' : ''}`}: ${qs.join(' ')}`
    const batch: MessageBatch = {
      id: nid('msg_batch_sim_'), cycle_id: cycleId, exception_ids: exceptionIds, intended_respondent_role: role,
      intended_respondent_label: role.replace('_', ' '), actual_recipient: '***-**00', channel: 'imessage', text,
      text_hash: await sha256(text), approval_id: null, state: 'draft', provider_message_id: null, sent_at: null,
      provider_status: null, provenance: 'synthetic',
    }
    S.batches.push(batch)
    for (const e of list) setState(e, 'investigating', 'owner approves the drafted question')
    emit('resolution', 'message.drafted', `Drafted ${followUp ? 'follow-up' : 'question'} for ${exceptionIds.length} exception(s)`, { batch_id: batch.id, exception_ids: exceptionIds })
    return clone(batch)
  },

  async editDraft(batchId: string, text: string) {
    const b = S.batches.find((x) => x.id === batchId)
    if (!b || b.state === 'sent') throw new Error('only unsent drafts can be edited')
    b.text = text
    b.text_hash = await sha256(text)
    const a = S.approvals.find((x) => x.id === b.approval_id)
    if (a && a.target_version !== b.text_hash) {
      a.state = 'invalidated'
      a.invalidated_reason = 'message text changed after approval'
      b.approval_id = null
      b.state = 'draft'
      emit('system', 'approval.invalidated', `Approval ${a.id} invalidated: text changed`, { approval_id: a.id, batch_id: b.id })
    }
  },

  approve(input: { kind: Approval['kind']; target_id: string; target_version: string; scope_text: string }): Approval {
    const a: Approval = {
      id: nid('appr_sim_'), kind: input.kind, target_id: input.target_id, target_version: input.target_version, approver: 'owner',
      approved_at: now(), scope_text: input.scope_text, state: 'active', invalidated_reason: null,
    }
    S.approvals.push(a)
    const b = S.batches.find((x) => x.id === input.target_id)
    if (b) { b.approval_id = a.id; b.state = 'approved' }
    const c = S.corrections.find((x) => x.id === input.target_id)
    if (c) { c.approval_id = a.id; c.state = 'approved' }
    emit('owner', 'approval.granted', `Owner approved ${input.kind.replace('_', ' ')} ${input.target_id}`, { approval_id: a.id, target_id: a.target_id })
    return clone(a)
  },

  send(batchId: string): MessageBatch {
    const b = S.batches.find((x) => x.id === batchId)
    if (!b) throw new Error('batch not found')
    if (b.state === 'sent') return clone(b) // a batch sends once
    const a = S.approvals.find((x) => x.id === b.approval_id)
    if (!a || a.state !== 'active' || a.target_version !== b.text_hash) throw new Error('send refused: no active approval for this exact text')
    b.state = 'sent'
    b.sent_at = now()
    b.provider_message_id = nid('fake_')
    b.provider_status = 'fixture simulation: not sent through Photon'
    for (const id of b.exception_ids) setState(exc(id), 'awaiting_reply', 'wait for reply')
    emit('resolution', 'message.sent', `Sent batch to ${b.intended_respondent_label} (fixture simulation)`, { batch_id: b.id })
    return clone(b)
  },

  // Replays the scripted lane B reply that matches this batch's categories (replies_v1.json).
  simulateReply(batchId: string) {
    const b = S.batches.find((x) => x.id === batchId)
    if (!b || b.state !== 'sent') throw new Error('batch must be sent first')
    const list = b.exception_ids.map(exc)
    const byCat = new Map(list.map((e) => [e.category as string, e.id]))
    const resolve = (ph: string) => byCat.get(ph.replace(/[{}]/g, ''))
    const cats = new Set(byCat.keys())
    const candidates = bundle.replies.filter((r) => !S.usedReplies.has(r.name)
      && r.batch_exception_ids.every((ph) => cats.has(ph.replace(/[{}]/g, ''))))
    const exact = candidates.find((r) => r.batch_exception_ids.length === cats.size) ?? candidates[0]
    let raw: string
    let statuses: Record<string, Status> = {}
    let extracted: Record<string, Record<string, unknown>> = {}
    let needs: string[] = []
    let blocked = false
    let label: string
    if (exact) {
      S.usedReplies.add(exact.name)
      label = exact.name
      raw = exact.raw_text
      const ex = exact.expect as { statuses?: Record<string, Status>; extracted?: Record<string, Record<string, unknown>>; needs_clarification?: string[]; blocked_event?: string }
      for (const [ph, st] of Object.entries(ex.statuses ?? {})) { const id = resolve(ph); if (id) statuses[id] = st }
      for (const [ph, v] of Object.entries(ex.extracted ?? {})) { const id = resolve(ph); if (id) extracted[id] = v }
      needs = (ex.needs_clarification ?? []).map(resolve).filter((x): x is string => !!x)
      blocked = ex.blocked_event === 'blocked.unauthorized_instruction'
    } else if (list.some((e) => e.category === 'already_paid_allocation')) {
      // Follow-up after the scripted conflicting reply: confirms lane B's T02 correction target.
      const e = list.find((x) => x.category === 'already_paid_allocation')!
      label = 'simulated follow-up confirmation (fixture)'
      raw = 'Checked the schedule: the 10/01 shift was Job 02.'
      statuses = { [e.id]: 'answered' }
      extracted = { [e.id]: { ...T02.after } }
    } else {
      throw new Error('No scripted test reply in the fixtures for this question')
    }
    const inbound: InboundMessage = {
      id: nid('msg_in_sim_'), provider_message_id: nid('fake_in_'), sender: '***-**00', received_at: now(), raw_text: raw,
      correlated_batch_id: b.id, dedupe_key: '', respondent_actual: 'owner_test_phone', respondent_intended_role: b.intended_respondent_role,
      provenance: 'test_reply',
    }
    inbound.dedupe_key = inbound.provider_message_id
    S.inbound.push(inbound)
    emit('bridge', 'message.received', `Test reply received (${label})`, { inbound_id: inbound.id, batch_id: b.id })
    const parsed: ParsedReply = {
      inbound_id: inbound.id,
      answers: list.map((e) => ({
        exception_id: e.id, status: statuses[e.id] ?? 'unaddressed', extracted: extracted[e.id] ?? {},
        confidence: statuses[e.id] === 'answered' ? 0.9 : 0.3, quote: raw,
      })),
      needs_clarification: needs, model: 'fixture (no model call)', schema_version: '1',
    }
    S.parsed.push(parsed)
    emit('resolution', 'reply.parsed', `Parsed reply: ${parsed.answers.map((a) => a.status).join(', ')}`, { inbound_id: inbound.id })
    if (blocked) {
      S.blocked.add(inbound.id)
      emit('system', 'blocked.unauthorized_instruction', 'Reply contained instructions; treated as data and blocked', { inbound_id: inbound.id, batch_id: b.id })
    }
    if (needs.length) emit('resolution', 'clarification.needed', `${needs.length} question(s) need clarification`, { exception_ids: needs })
    for (const a of parsed.answers) {
      const e = exc(a.exception_id)
      if (a.status === 'answered') {
        const r: Resolution = {
          id: nid('res_sim_'), exception_id: e.id, cycle_id: cycleId, confirmed_facts: a.extracted, evidence: e.evidence,
          inbound_ids: [inbound.id], confirmer_actual: 'owner_test_phone', confirmer_intended_role: b.intended_respondent_role,
          scope: { company_label: bundle.cycle.company_label, cycle_id: cycleId }, approved_correction_id: null, created_at: now(), memory_ref: null,
        }
        S.resolutions = S.resolutions.filter((x) => x.exception_id !== e.id).concat(r)
        e.resolution_id = r.id
        emit('resolution', 'resolution.recorded', `Resolution recorded for ${e.id}`, { exception_id: e.id, resolution_id: r.id })
        setState(e, 'needs_approval', 'propose a correction for owner approval')
      } else if (a.status === 'conflicting') setState(e, 'conflicting', 'clarify with a bounded follow-up')
      else if (a.status === 'unaddressed') setState(e, 'awaiting_reply', blocked ? 'instruction blocked; question still open' : 'still waiting for an answer')
      else setState(e, 'answer_received', 'clarify with a bounded follow-up')
    }
  },

  stop() {
    emit('owner', 'run.stopped', 'Owner stopped the run; new actions cancelled, pending approvals kept', { pending_approvals_kept: true })
    return { stopped: true }
  },

  proposeCorrection(resolutionId: string, kind: LocalCorrection['kind'], after: Record<string, unknown>): LocalCorrection {
    const r = S.resolutions.find((x) => x.id === resolutionId)
    if (!r) throw new Error('resolution not found')
    const isT02 = exc(r.exception_id).category === 'already_paid_allocation'
    const c: LocalCorrection = {
      id: nid('corr_sim_'), resolution_id: r.id, kind: isT02 ? T02.kind : kind,
      before: isT02 ? clone(T02.before) : {}, after: isT02 ? clone(T02.after) : after,
      calculation_impact: isT02 ? clone(T02.calculation_impact) : {},
      approval_id: null, state: 'proposed', applied_at: null,
    }
    S.corrections.push(c)
    emit('payroll', 'correction.proposed', `Proposed ${c.kind.replace('_', ' ')} for ${r.exception_id}`, { correction_id: c.id })
    return clone(c)
  },

  applyCorrection(id: string) {
    const c = S.corrections.find((x) => x.id === id)
    if (!c) throw new Error('correction not found')
    const a = S.approvals.find((x) => x.id === c.approval_id)
    if (!a || a.state !== 'active' || a.kind !== 'local_correction') throw new Error('apply refused: correction not approved')
    c.state = 'applied'
    c.applied_at = now()
    const r = S.resolutions.find((x) => x.id === c.resolution_id)!
    r.approved_correction_id = c.id
    const e = exc(r.exception_id)
    setState(e, 'resolved', 'none')
    emit('payroll', 'correction.applied', `Applied local correction ${c.id} (not a source write)`, { correction_id: c.id })
    emit('payroll', 'recalc.completed', 'Recalculated readiness from fixture matrix', {})
    if (e.category === 'already_paid_allocation') {
      S.readiness = clone(bundle.readiness_after_t02)
      emit('payroll', 'readiness.changed', 'Quote commission blockers updated after T02 correction', {})
    }
  },
}
