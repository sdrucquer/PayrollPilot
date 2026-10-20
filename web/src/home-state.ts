import type { Packet, Thread } from './api'
import type { CompensationItem, LocalCorrection, MessageBatch, PayrollCycle, PayrollException, PPEvent, ReadinessResponse } from './contracts'

interface PacketTotals { workers_in_cycle?: number; workers_review_ready?: number; stage1_gross_all_cents?: number | null; stage1_gross_ready_cents?: number | null; entries_in_cycle?: number }
interface PacketEarning { worker_id: string; display_name?: string; gross_new_cents?: number | null; readiness?: { state: string; scope: string } }
type HomePacket = Packet & { totals?: PacketTotals; earnings?: PacketEarning[]; draft_version?: string }

export interface Data {
  cycle: PayrollCycle; readiness: ReadinessResponse; exceptions: PayrollException[]; events: PPEvent[]
  packet: HomePacket | null; threads: Thread[]; stopped: boolean; messagingMode?: string
}

export const ROLE: Record<string, string> = { ops_lead: 'Ops lead', owner: 'you', worker: 'a worker', quoter: 'the quoter', accountant: 'the accountant' }
export const KIND_NAME: Record<string, string> = { quote_commission: 'commission', marketing: 'marketing bonus', tip: 'tips', manager_pool: 'manager pool' }
const plural = (n: number, w: string) => `${n} ${w}${n === 1 ? '' : 's'}`

// ---- derived, display-only state ----
export function wagesLine(d: Data): { ok: boolean; text: string } {
  const r = d.readiness.stage1
  const workers = Object.values(d.readiness.workers ?? {})
  const total = workers.length
  const ready = workers.filter((w) => w.state === 'ready').length
  const answers = new Set(r.blockers.filter((b) => b.exception_id).map((b) => b.exception_id)).size
  if (r.state === 'ready') return { ok: true, text: total ? `verified for all ${total} workers.` : 'ready for review.' }
  const head = total ? `ready for ${ready} of ${total} workers.` : `${r.scope.replace(/\.$/, '')}.`
  return { ok: false, text: `${head} ${answers ? `${plural(answers, 'answer')} needed.` : ''}`.trim() }
}

export function stage2Line(items: CompensationItem[]): { ok: boolean; text: string } {
  const s2 = items.filter((i) => i.kind !== 'wages')
  const ready = s2.filter((i) => i.readiness.state === 'ready')
  const open = s2.filter((i) => !['ready', 'not_meaningful'].includes(i.readiness.state))
  const bl = open.flatMap((i) => i.readiness.blockers)
  const answers = new Set(bl.filter((b) => b.exception_id).map((b) => b.exception_id)).size
  const decisions = new Set(bl.filter((b) => !b.exception_id && b.code.startsWith('policy_missing')).map((b) => b.code)).size
  const names = [...new Set(open.map((i) => KIND_NAME[i.kind]))]
  const parts: string[] = []
  for (const kind of [...new Set(ready.map((i) => i.kind))]) {
    const count = ready.filter((i) => i.kind === kind).length
    parts.push(`${plural(count, KIND_NAME[kind] ?? 'item')} ready.`)
  }
  if (open.length) {
    const wait = [answers && plural(answers, 'answer'), decisions && `${plural(decisions, 'decision')} from you`].filter(Boolean).join(' and ')
    parts.push(`${names.join(', ').replace(/^./, (c) => c.toUpperCase())} waiting${wait ? ` on ${wait}` : ''}.`)
  }
  return { ok: s2.length > 0 && open.length === 0, text: parts.join(' ') || 'No items reported.' }
}

export type Pending =
  | { kind: 'message'; batch: MessageBatch; exceptions: PayrollException[] }
  | { kind: 'correction'; correction: LocalCorrection & { target_version?: string }; exception: PayrollException }
  | { kind: 'draft'; role: string; exceptions: PayrollException[] }
  | null

export function findPending(d: Data, declined: Set<string>): Pending {
  for (const t of d.threads) {
    const b = t.batches.find((x) => (x.state === 'draft' || x.state === 'approved') && !x.declined_at && !declined.has(x.id))
    if (b) return { kind: 'message', batch: b, exceptions: d.exceptions.filter((e) => b.exception_ids.includes(e.id)) }
  }
  for (const t of d.threads) {
    if (t.correction && (t.correction.state === 'proposed' || t.correction.state === 'approved') && !declined.has(t.correction.id))
      return { kind: 'correction', correction: t.correction, exception: t.exception }
  }
  const unsent = d.exceptions.filter((e) => e.state === 'detected' && e.intended_respondent_role !== 'owner')
  if (unsent.length) {
    const ops = unsent.filter((e) => e.intended_respondent_role === 'ops_lead')
    const list = ops.length ? ops : unsent.filter((e) => e.intended_respondent_role === unsent[0].intended_respondent_role)
    return { kind: 'draft', role: list[0].intended_respondent_role, exceptions: list }
  }
  return null
}

export const STEP_NAMES = ['Gather employee hours', 'Audit hours', 'Resolve missing information', 'Prepare employee wages', 'Reconcile job expenses and commissions', 'Payroll ready for your review']
export const SHORT = ['Gather', 'Audit', 'Resolve', 'Prepare', 'Reconcile', 'Ready for review']

export function steps(d: Data, pending: Pending) {
  const ev = (t: string) => [...d.events].reverse().find((e) => e.type === t)
  const s1 = d.cycle.stage1.state
  const s2 = d.cycle.stage2.state
  const reviewed = (state: string) => ['review_ready', 'owner_approved'].includes(state)
  const s1ready = d.readiness.stage1.state === 'ready'
  const s1review = s1ready && reviewed(s1)
  const s2review = reviewed(s2)
  const gather = ev('snapshot.captured')
  const audit = ev('audit.completed')
  const done = [!!gather || ['auditing', 'resolving'].includes(s1) || s1review,
    !!audit || s1 === 'resolving' || s1review, s1ready, s1review,
    s1review && s2review, s1review && s2review && !pending]
  for (let i = 1; i < done.length; i++) done[i] = done[i] && done[i - 1]
  const cur = done.findIndex((x) => !x)
  const times = [gather?.at, audit?.at, ev('correction.applied')?.at, ev('readiness.changed')?.at, undefined, undefined]
  const doneCount = done.filter(Boolean).length
  const ready = doneCount === 6
  return { done, cur, times, doneCount, ready }
}

export function currentSub(d: Data, idx: number, pending: Pending): string {
  const total = d.exceptions.length
  const resolved = d.exceptions.filter((e) => e.state === 'resolved').length
  const waiting = d.exceptions.filter((e) => e.state === 'awaiting_reply')
  if (idx === 2) {
    const tail = pending?.kind === 'message' ? `Waiting on your approval to text the ${ROLE[pending.batch.intended_respondent_role] ?? 'respondent'}.`
      : pending?.kind === 'correction' ? 'Waiting on your approval of a correction.'
      : waiting.length ? `Waiting on the ${ROLE[waiting[0].intended_respondent_role] ?? 'respondent'} to reply.`
      : pending?.kind === 'draft' ? `${plural(pending.exceptions.length, 'question')} ready to draft for the ${ROLE[pending.role]}.` : ''
    return `${resolved} of ${total} answered. ${tail}`.trim()
  }
  if (idx === 0) return 'Loading the pay-period snapshot.'
  if (idx === 1) return 'Checking every timesheet against jobs, schedules and rates.'
  if (idx === 3) return 'Recalculating wages with the confirmed answers.'
  if (idx === 4) return 'Commissions, tips and manager pool, each on its own.'
  return 'You approve the draft. Gusto stays "not prepared".'
}

export interface ActRow { id: string; at: string; icon: 'chat' | 'send' | 'reply' | 'check' | 'search' | 'doc' | 'pause' | 'shield'; text: string; test?: boolean }
export function activity(d: Data): ActRow[] {
  const rows: ActRow[] = []
  const ordered = [...d.events].sort((a, b) => a.at.localeCompare(b.at))
  const snap = ordered.find((e) => e.type === 'snapshot.captured')
  const entries = (snap?.refs?.counts as { time_entries?: number } | undefined)?.time_entries ?? d.packet?.totals?.entries_in_cycle
  const detected = d.events.filter((e) => e.type === 'exception.detected')
  const missing = d.exceptions.filter((e) => e.category === 'missing_job').length
  for (const e of ordered) {
    const role = (e.refs?.respondent_role as string | undefined) ?? d.threads.flatMap((t) => t.batches).find((b) => b.id === e.refs.batch_id)?.intended_respondent_role ?? 'ops_lead'
    const who = ROLE[role] === 'you' ? 'you' : `the ${ROLE[role] ?? 'Ops lead'}`
    switch (e.type) {
      case 'audit.completed':
        rows.push({ id: e.id, at: e.at, icon: 'doc', text: entries ? `Checked ${entries} timesheets` : 'Checked the timesheets' })
        if (detected.length || d.exceptions.length) {
          const n = detected.length || d.exceptions.length
          rows.push({ id: e.id + '-f', at: e.at, icon: 'search', text: `Found ${plural(n, 'thing')} to check${missing ? `, including ${plural(missing, 'missing job assignment')}` : ''}` })
        }
        break
      case 'message.drafted': rows.push({ id: e.id, at: e.at, icon: 'chat', text: `Drafted questions for ${who}` }); break
      case 'approval.invalidated': if (e.refs.decision === 'declined') rows.push({ id: e.id, at: e.at, icon: 'pause', text: 'You declined a message draft. Nothing was sent.' }); break
      case 'message.sent': rows.push({ id: e.id, at: e.at, icon: 'send', text: `Sent your approved question to ${who}` }); break
      case 'message.received': {
        const reply = d.threads.flatMap((t) => t.inbound).find((i) => i.id === e.refs.inbound_id)
        const replyRole = reply?.respondent_intended_role ?? role
        rows.push({ id: e.id, at: e.at, icon: 'reply', text: `${ROLE[replyRole] === 'you' ? 'You' : (ROLE[replyRole] ?? 'Respondent')} replied`, test: reply?.provenance === 'test_reply' || e.refs.provenance === 'test_reply' }); break
      }
      case 'clarification.needed': rows.push({ id: e.id, at: e.at, icon: 'chat', text: 'The reply needs clarification' }); break
      case 'correction.applied': rows.push({ id: e.id, at: e.at, icon: 'check', text: 'Applied your approved local correction' }); break
      case 'readiness.changed': rows.push({ id: e.id, at: e.at, icon: 'check', text: d.readiness.stage1.state === 'ready' ? 'Employee wages ready for review' : 'Updated payroll readiness' }); break
      case 'blocked.unauthorized_instruction': rows.push({ id: e.id, at: e.at, icon: 'shield', text: 'Ignored instructions inside a reply; nothing was acted on' }); break
      case 'workbook.generated': rows.push({ id: e.id, at: e.at, icon: 'doc', text: 'Built the review workbook' }); break
      case 'run.stopped': rows.push({ id: e.id, at: e.at, icon: 'pause', text: 'Paused by you' }); break
    }
  }
  return rows.reverse().slice(0, 7)
}
