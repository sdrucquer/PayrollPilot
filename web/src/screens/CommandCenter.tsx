// One screen, three zones (docs/UI-ONE-SCREEN.md): where are the agents, and what is limiting payroll?
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, DEFAULT_CYCLE_ID, type Packet } from '../api'
import type {
  CompKind, CompensationItem, Health, PayrollCycle, PayrollException, PPEvent, ReadinessResponse, WorkbookArtifact, Worker,
} from '../contracts'
import { formatCents, formatMinutes, formatTime, humanize } from '../format'
import { STAGE2, stage2Summary } from '../summary'
import { ErrorBox, Loading, ProvenanceTag, StateTag } from '../components/ui'
import Thread from './Thread'

interface Data {
  cycle: PayrollCycle; readiness: ReadinessResponse; workers: Worker[]; exceptions: PayrollException[]
  events: PPEvent[]; health: Health | null; packet: Packet | null
}

const STEPS: { name: string; agent: string; match: (e: PPEvent) => boolean }[] = [
  { name: 'Collect', agent: 'System', match: (e) => ['cycle.created', 'snapshot.captured'].includes(e.type) },
  { name: 'Audit', agent: 'Audit agent', match: (e) => e.actor === 'audit' },
  { name: 'Resolve', agent: 'Resolution agent', match: (e) => e.actor === 'resolution' || e.actor === 'bridge' },
  { name: 'Prepare', agent: 'Payroll Prep agent', match: (e) => e.actor === 'payroll' },
  { name: 'Review', agent: 'Owner', match: (e) => e.actor === 'owner' },
]

const ROLE_GROUPS: { role: PayrollException['intended_respondent_role']; label: string }[] = [
  { role: 'ops_lead', label: 'Ops lead' },
  { role: 'worker', label: 'Workers' },
  { role: 'quoter', label: 'Quoters' },
  { role: 'accountant', label: 'Accountant' },
  { role: 'owner', label: 'Owner (you)' },
]

const ROW_STATE: Record<PayrollException['state'], string> = {
  detected: 'not asked yet', investigating: 'draft', awaiting_reply: 'sent, awaiting reply', answer_received: 'answered',
  needs_approval: 'needs approval', needs_source_verification: 'needs source check', resolved: 'resolved',
  conflicting: 'needs clarification', insufficient_evidence: 'insufficient evidence', escalated: 'escalated',
}

function chipTone(items: CompensationItem[]): string {
  const st = items.map((i) => i.readiness.state)
  if (st.includes('blocked')) return 'blocked'
  if (st.includes('partial')) return 'partial'
  if (st.length > 0 && st.every((s) => s === 'ready')) return 'ready'
  return 'pending'
}

function Pipeline({ events }: { events: PPEvent[] }) {
  const last = STEPS.map((s) => [...events].reverse().find(s.match))
  const latestAt = Math.max(...last.map((e) => (e ? new Date(e.at).getTime() : 0)))
  return (
    <div className="pipeline" aria-label="Cycle progress">
      {STEPS.map((s, i) => {
        const e = last[i]
        const cls = !e ? '' : new Date(e.at).getTime() === latestAt ? 'active' : 'ran'
        return (
          <div key={s.name} className={`step ${cls}`}>
            <div className="bar"><i /></div>
            <div className="name">{s.name} <span className="agent">{s.agent}</span></div>
            <div className="last">{e ? <>{e.summary} <span className="tiny">{formatTime(e.at)}</span></> : <span className="tiny">no activity yet</span>}</div>
          </div>
        )
      })}
    </div>
  )
}

function Stage1Row({ d, names }: { d: Data; names: Map<string, Worker> }) {
  const [open, setOpen] = useState(false)
  const r = d.readiness.stage1
  const wages = d.readiness.items.filter((i) => i.kind === 'wages')
  const pk = new Map((d.packet?.workers ?? []).map((w) => [w.worker_id ?? w.id ?? '', w]))
  return (
    <div className="rrow">
      <div className="rrow-head">
        <span className="badge-s">S1</span><h3>Employee wages</h3>
        <StateTag value={r.state} kind="ready" />
        <ProvenanceTag value={d.cycle.provenance} />
      </div>
      <div>{r.scope}</div>
      <div className="muted small">{r.blockers.length} blocker{r.blockers.length === 1 ? '' : 's'}{r.unknown_amount ? ' · amount unknown until they clear' : ''}</div>
      <div className="chips" style={{ marginTop: 8 }}>
        <span className="chip"><span className="dot" style={{ color: r.state === 'ready' ? 'var(--ready)' : 'var(--partial)' }} />Wage correctness: {humanize(r.state)}</span>
        <span className="chip"><span className="dot" style={{ color: 'var(--pending)' }} />Labor/revenue review: not reviewed</span>
        <span className="chip"><span className="dot" style={{ color: 'var(--blocked)' }} />Cash confirmation: not confirmed</span>
      </div>
      <button className="expand" onClick={() => setOpen((o) => !o)}>{open ? 'Hide' : 'Show'} per-worker table</button>
      {open && (
        <table className="table">
          <thead><tr><th>Worker</th><th className="num">Minutes</th><th>Rate</th><th className="num">Gross</th><th>Readiness</th></tr></thead>
          <tbody>
            {wages.map((i) => {
              const w = i.worker_id ? names.get(i.worker_id) : undefined
              const p = i.worker_id ? pk.get(i.worker_id) : undefined
              const rate = p?.rate_status ?? (w as Worker & { rates?: { status: string }[] } | undefined)?.rates?.[0]?.status
              const gross = p?.gross_cents ?? (i.computed?.gross_cents as number | null | undefined) ?? null
              return (
                <tr key={i.id}>
                  <td>{p?.display_name ?? w?.display_name ?? i.worker_id ?? '—'}<div className="tiny">{i.readiness.scope}</div></td>
                  <td className="num">{formatMinutes(p?.total_minutes ?? p?.minutes ?? null)}</td>
                  <td>{rate ? humanize(rate) : '—'}</td>
                  <td className="num">{formatCents(gross)}</td>
                  <td><StateTag value={i.readiness.state} kind="ready" /></td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
      {open && !d.packet && <p className="tiny">Minutes come from the review packet, which is not available yet; shown as a dash.</p>}
    </div>
  )
}

function Stage2Row({ d }: { d: Data }) {
  const items = d.readiness.items.filter((i) => i.kind !== 'wages')
  const kinds = STAGE2.filter(({ kind }) => kind !== 'marketing' || items.some((i) => i.kind === kind))
  return (
    <div className="rrow">
      <div className="rrow-head"><span className="badge-s">S2</span><h3>Additional compensation</h3></div>
      <div className="small muted">{stage2Summary(items)}</div>
      <div className="s2chips">
        {kinds.map(({ kind, title }: { kind: CompKind; title: string }) => {
          const ofKind = items.filter((i) => i.kind === kind)
          const counts = new Map<string, number>()
          for (const i of ofKind) counts.set(i.readiness.state, (counts.get(i.readiness.state) ?? 0) + 1)
          const all = ofKind.flatMap((i) => i.readiness.blockers)
          const first = all[0]
          return (
            <div key={kind} className={`s2chip ${chipTone(ofKind)}`}>
              <span className="t">{title}</span>
              <span className="row wrap">{ofKind.length === 0 ? <span className="tiny">no item reported</span>
                : [...counts].map(([st, n]) => <StateTag key={st} value={st} kind="ready" label={`${n} ${humanize(st)}`} />)}</span>
              <span className="tiny">{all.length} blocker{all.length === 1 ? '' : 's'}</span>
              {first && (first.exception_id
                ? <Link className="b" to={`/e/${first.exception_id}`}>{first.label}</Link>
                : <span className="b">{first.label} <code>{first.code}</code></span>)}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ActivityLog({ events }: { events: PPEvent[] }) {
  const [open, setOpen] = useState(false)
  const [actor, setActor] = useState('')
  const list = [...events].reverse().filter((e) => !actor || e.actor === actor)
  return (
    <div>
      <button className="expand" onClick={() => setOpen((o) => !o)}>{open ? 'Hide' : 'Show'} agent activity log ({events.length})</button>
      {open && (
        <>
          <div className="filters" style={{ marginTop: 8 }}>
            {['', 'audit', 'resolution', 'payroll', 'owner', 'system', 'bridge'].map((a) => (
              <button key={a} className={`pill ${actor === a ? 'on' : ''}`} onClick={() => setActor(a)}>{a ? humanize(a) : 'All'}</button>
            ))}
          </div>
          <ul className="log">
            {list.map((e) => (
              <li key={e.id} className={e.type === 'memory.applied' || e.type.startsWith('handoff.') || e.type === 'blocked.unauthorized_instruction' ? 'hl' : ''}>
                <span className={`actor actor-${e.actor}`}>{e.actor}</span>
                <span className="tiny lt">{formatTime(e.at)}</span>
                <code className="ly">{e.type}</code>
                <span>{e.summary}
                  {e.usage && <span className="tiny"> · {e.usage.model} · {e.usage.input_tokens} in / {e.usage.output_tokens} out · ${e.usage.cost_usd.toFixed(4)}</span>}
                  {e.duration_ms !== null && <span className="tiny"> · {e.duration_ms} ms</span>}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

function Zone2({ d, selected, names, onChange }: { d: Data; selected?: string; names: Map<string, Worker>; onChange: () => void }) {
  const nav = useNavigate()
  const [err, setErr] = useState<unknown>(null)
  const [showResolved, setShowResolved] = useState(false)
  const open = d.exceptions.filter((e) => e.state !== 'resolved')
  const resolved = d.exceptions.filter((e) => e.state === 'resolved')
  const blocks = (e: PayrollException) => {
    const parts: string[] = []
    const w = e.entity_refs.worker_id ? names.get(e.entity_refs.worker_id)?.display_name ?? e.entity_refs.worker_id : null
    if (e.stage_impact.stage1_wages !== 'none') parts.push(`wages${w ? ` for ${w}` : ''}`)
    if (e.stage_impact.stage2_costs !== 'none') parts.push(`${humanize(e.stage_impact.stage2_costs)}${e.entity_refs.job_ids?.length ? ` (${e.entity_refs.job_ids.join(', ')})` : ''}`)
    return parts.join(' · ') || 'no stage impact'
  }
  const ref = (e: PayrollException) => e.evidence[0] ? `${e.evidence[0].system}:${e.evidence[0].record_id}`
    : [...(e.entity_refs.time_entry_ids ?? []), ...(e.entity_refs.cost_ids ?? []), ...(e.entity_refs.coverage ?? [])][0] ?? null

  async function draftGroup(ids: string[]) {
    setErr(null)
    try { await api.draft(ids); onChange(); nav(`/e/${ids[0]}`) } catch (x) { setErr(x) }
  }

  return (
    <section className="zone2">
      <div className="group-head" style={{ paddingTop: 0 }}>
        <h3>What's limiting payroll <span className="count">{open.length} open</span></h3>
        <span className="muted small">grouped by who we're waiting on</span>
      </div>
      {err != null && <ErrorBox error={err} />}
      {ROLE_GROUPS.map(({ role, label }) => {
        const rows = open.filter((e) => e.intended_respondent_role === role)
        if (rows.length === 0) return null
        const unsent = rows.filter((e) => e.state === 'detected')
        const waiting = rows.filter((e) => e.state === 'awaiting_reply')
        const since = waiting.map((e) => e.updated_at).sort()[0]
        const isOwner = role === 'owner'
        return (
          <div key={role} className="group">
            <div className="group-head">
              <div>
                <h3>{label} <span className="count">{rows.length}</span></h3>
                <div className="muted small">
                  {isOwner ? `${rows.length} decision${rows.length === 1 ? '' : 's'} for you` : `${rows.length} question${rows.length === 1 ? '' : 's'}`}
                  {waiting.length > 0 && ` · ${waiting.length} awaiting reply since ${formatTime(since)}`}
                  {unsent.length > 0 && !isOwner && ` · ${unsent.length} not asked yet`}
                </div>
              </div>
              {!isOwner && unsent.length > 0 && (
                <button className="btn primary" onClick={() => draftGroup(unsent.map((e) => e.id))}>Draft one message</button>
              )}
            </div>
            <ul className="exc-list">
              {rows.map((e) => (
                <li key={e.id} className={e.id === selected ? 'active' : ''}>
                  <Link to={`/e/${e.id}`} className="exc-link">
                    <span className="exc-title">{e.title}</span>
                    <span className="muted small">Blocks {blocks(e)}{ref(e) && <> · <code>{ref(e)}</code></>}</span>
                  </Link>
                  <div className="exc-side">
                    <StateTag value={e.state} kind="exc" label={isOwner && e.state === 'detected' ? (e.category === 'policy_missing' ? 'decide' : 'approve') : ROW_STATE[e.state]} />
                    <span className="small">{formatCents(e.dollars_affected_cents)}</span>
                    <ProvenanceTag value={e.provenance} />
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )
      })}
      <div className="group">
        <div className="group-head">
          <h3>Resolved this cycle <span className="count">{resolved.length}</span></h3>
          {resolved.length > 0 && <button className="expand" onClick={() => setShowResolved((s) => !s)}>{showResolved ? 'Hide' : 'Show'}</button>}
        </div>
        {showResolved && (
          <ul className="exc-list">
            {resolved.map((e) => (
              <li key={e.id} className={e.id === selected ? 'active' : ''}>
                <Link to={`/e/${e.id}`} className="exc-link"><span className="exc-title">{e.title}</span></Link>
                <div className="exc-side"><StateTag value="resolved" kind="exc" /></div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

export default function CommandCenter() {
  const { id } = useParams()
  const cycleId = DEFAULT_CYCLE_ID
  const [d, setD] = useState<Data | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [tick, setTick] = useState(0)
  const [toast, setToast] = useState<{ wb?: WorkbookArtifact; err?: unknown; text?: string } | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let live = true
    Promise.all([
      api.cycle(cycleId), api.readiness(cycleId), api.workers(cycleId), api.exceptions(cycleId),
      api.events(cycleId).catch(() => [] as PPEvent[]), api.health().catch(() => null), api.packet(cycleId),
    ]).then(([cycle, readiness, workers, exceptions, events, health, packet]) => {
      if (live) { setD({ cycle, readiness, workers, exceptions, events, health, packet }); setError(null) }
    }).catch((e) => live && setError(e))
    return () => { live = false }
  }, [cycleId, tick])

  // In api mode, replies arrive from the bridge at any time: refresh every 4 s.
  useEffect(() => {
    if (api.mode !== 'api') return
    const t = setInterval(() => setTick((x) => x + 1), 4000)
    return () => clearInterval(t)
  }, [])

  const names = useMemo(() => new Map((d?.workers ?? []).map((w) => [w.id, w])), [d])
  if (error && !d) return <ErrorBox error={error} />
  if (!d) return <Loading />
  const c = d.cycle
  const incomplete = c.coverage.filter((x) => !x.complete)
  const photon = d.health?.integrations.photon ?? 'unverified'
  const refresh = () => setTick((x) => x + 1)

  async function exportWorkbook() {
    setBusy(true)
    try { setToast({ wb: await api.workbook(cycleId) }); refresh() } catch (e) { setToast({ err: e }) } finally { setBusy(false) }
  }
  async function stop() {
    setBusy(true)
    try { await api.stop(); setToast({ text: 'Run stopped. New actions are cancelled; pending approvals stay pending.' }); refresh() } catch (e) { setToast({ err: e }) } finally { setBusy(false) }
  }

  return (
    <div className="stack">
      <section className="card zone1">
        <div className="cycle-title">
          <div>
            <h2>Payroll cycle · {c.period_start} to {c.period_end}</h2>
            <div className="muted small">{c.company_label} · payday {c.payday ?? '—'} · {c.business_tz} · existing run {humanize(c.existing_run_status)} · {c.policy_version}</div>
          </div>
          <div className="row wrap">
            <button className="btn" onClick={stop} disabled={busy}>Stop run</button>
            <button className="btn primary" onClick={exportWorkbook} disabled={busy}>Export workbook</button>
          </div>
        </div>
        <div className="chips">
          <span className="chip chip-warn"><span className="dot" /><span>Gusto: {humanize(c.destination)}</span></span>
          <span className="chip chip-info"><span className="dot" /><span>Data: {humanize(c.provenance)}{api.mode === 'fixture' ? ' fixture' : ''}</span></span>
          <span className={`chip ${photon === 'tested' ? 'chip-ok' : 'chip-warn'}`}><span className="dot" />
            <span>Messaging: {photon === 'tested' ? 'live Photon' : `Photon ${photon}`} · test mode · owner test phone only</span></span>
          <span className={`chip ${incomplete.length ? 'chip-bad' : 'chip-ok'}`}><span className="dot" />
            <span title={incomplete.map((x) => `${x.system}/${x.dataset}: ${x.incomplete_reason ?? 'incomplete'}`).join('\n')}>
              Coverage: {c.coverage.length} datasets · {incomplete.length} incomplete{incomplete[0] ? ` (${incomplete[0].system} ${humanize(incomplete[0].dataset)})` : ''}
            </span></span>
          <span className="chip"><span className="dot" style={{ color: 'var(--fg-3)' }} /><span>Submit payroll: unavailable</span></span>
        </div>
        <Pipeline events={d.events} />
        <div className="readiness-rows">
          <Stage1Row d={d} names={names} />
          <Stage2Row d={d} />
        </div>
        <ActivityLog events={d.events} />
      </section>

      <div className={`zones ${id ? 'has-thread' : ''}`}>
        <Zone2 d={d} selected={id} names={names} onChange={refresh} />
        {id ? <Thread key={id} id={id} onChange={refresh} />
          : <section className="thread empty muted">Select a blocker to see its evidence, the question, the reply and the correction.</section>}
      </div>

      {toast && (
        <div className="toast" role="status">
          {toast.wb && (
            <>
              <strong>Workbook generated</strong>
              <span>Draft version <code>{toast.wb.draft_version}</code> · {toast.wb.sheets.length} sheets</span>
              <span>Verified totals: {Object.keys(toast.wb.verified_totals).length ? Object.entries(toast.wb.verified_totals).map(([k, v]) => `${humanize(k)} ${k.endsWith('_cents') ? formatCents(v as number | null) : String(v)}`).join(' · ') : 'none reported'}</span>
              <span className="warn">Original workbook not updated. {toast.wb.note}</span>
            </>
          )}
          {toast.text && <span>{toast.text}</span>}
          {toast.err != null && <ErrorBox error={toast.err} />}
          <button className="btn ghost" onClick={() => setToast(null)}>Dismiss</button>
        </div>
      )}
    </div>
  )
}
