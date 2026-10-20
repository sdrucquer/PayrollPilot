// Owner home page (docs/UI-ONE-SCREEN.md v2, lane G design/home.html + design/ready.html).
// Renders only what the API returns: money and minutes are formatted, never computed.
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, DEFAULT_CYCLE_ID } from '../api'
import type { LocalCorrection, PayrollException } from '../contracts'
import { activity, findPending, steps, wagesLine, stage2Line, ROLE, KIND_NAME, STEP_NAMES, SHORT, currentSub, type Data, type ActRow } from '../home-state'
import { formatCents, maskHandle, maskText } from '../format'
import { sha256 } from '../sim'
import '../home.css'
import BetweenPayrolls from './BetweenPayrolls'
import { idleHomeFor } from '../idle-state'

const time = (ts?: string) => ts ? new Date(ts).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }).replace(/ [AP]M$/, '') : ''
const day = (d: string) => new Date(`${d}T12:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
const dots = (h: string) => maskHandle(h).replace(/\*/g, '•')
const plural = (n: number, w: string) => `${n} ${w}${n === 1 ? '' : 's'}`

function Money({ cents }: { cents: number | null | undefined }) {
  const s = formatCents(cents)
  if (s === '—') return <span className="h-money">—</span>
  const [whole, frac] = s.split('.')
  return <span className="h-money">{whole}<span className="c">.{frac}</span></span>
}

const Check = ({ c = '#1F8A3B', s = 11 }: { c?: string; s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 16 16" fill="none" stroke={c} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 8.5l3.5 3.5 7-8" /></svg>
)
const Logo = ({ s = 15 }: { s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 16 16" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 12.5 8 3l5 9.5" /><path d="M5.5 9.5h5" /></svg>
)

function ActIcon({ k }: { k: ActRow['icon'] }) {
  const p = { width: 14, height: 14, viewBox: '0 0 16 16', fill: 'none', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
  if (k === 'chat') return <span className="h-ico ico-blue"><svg {...p} stroke="#0066D6"><path d="M3 4h10v7H7l-3 2.5V11H3z" /></svg></span>
  if (k === 'send') return <span className="h-ico ico-blue"><svg {...p} stroke="#0066D6"><path d="M2 8l12-5-3 11-3-4.5L2 8z" /></svg></span>
  if (k === 'reply') return <span className="h-ico ico-gray">O</span>
  if (k === 'check') return <span className="h-ico ico-green"><Check s={14} /></span>
  if (k === 'search') return <span className="h-ico ico-orange"><svg {...p} stroke="#9A4D00"><circle cx="7" cy="7" r="4.2" /><path d="M10.2 10.2 14 14" /></svg></span>
  if (k === 'shield') return <span className="h-ico ico-orange"><svg {...p} stroke="#9A4D00"><path d="M8 2l5 2v4c0 3-2.2 5.2-5 6-2.8-.8-5-3-5-6V4z" /></svg></span>
  if (k === 'pause') return <span className="h-ico ico-gray"><svg {...p} stroke="#3A3A3C"><path d="M6 4v8M10 4v8" /></svg></span>
  return <span className="h-ico ico-gray"><svg {...p} stroke="#3A3A3C"><rect x="3" y="2.5" width="10" height="11" rx="1.5" /><path d="M5.5 6h5M5.5 9h5" /></svg></span>
}

function correctionSentence(c: LocalCorrection, e: PayrollException): { text: string; lines: [string, string][] } {
  const after = c.after as Record<string, unknown>
  const before = c.before as Record<string, unknown>
  const imp = c.calculation_impact as { stage1_wages_delta_cents?: number | null; job_costing_delta?: { job_id: string; labor_delta_cents: number | null }[] }
  let text = e.title
  if (c.kind === 'job_allocation' && after.job_id) text = `Move this shift${before.job_id ? ` from ${String(before.job_id).replace('job_', 'Job ')}` : ''} to ${String(after.job_id).replace('job_', 'Job ')}.`
  if (c.kind === 'rate_confirmation') text = 'Confirm this worker’s rate.'
  if (c.kind === 'cost_link') text = 'Link this cost to its job.'
  if (c.kind === 'identity_merge') text = 'Treat these two profiles as one worker.'
  const lines: [string, string][] = []
  if (imp.stage1_wages_delta_cents !== undefined) lines.push(['Wages', imp.stage1_wages_delta_cents === 0 ? 'unchanged' : formatCents(imp.stage1_wages_delta_cents)])
  for (const j of imp.job_costing_delta ?? []) {
    const v = j.labor_delta_cents
    lines.push([`${j.job_id.replace('job_', 'Job ')} labor cost`, v === null ? '—' : `${v > 0 ? '+' : ''}${formatCents(v)}`])
  }
  return { text, lines }
}

export default function Home() {
  const cycleId = DEFAULT_CYCLE_ID
  const [d, setD] = useState<Data | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [acting, setBusy] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const busy = acting || refreshing
  const [actErr, setActErr] = useState<unknown>(null)
  const [editing, setEditing] = useState<string | null>(null)
  const [declined, setDeclined] = useState<Set<string>>(() => {
    try { return new Set(JSON.parse(sessionStorage.getItem(`declined:${cycleId}`) ?? '[]')) } catch { return new Set() }
  })
  const [justSent, setJustSent] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)
  const [tick, setTick] = useState(0)
  const refresh = useCallback(() => { setRefreshing(true); setTick((x) => x + 1) }, [])

  useEffect(() => {
    let live = true
    ;(async () => {
      const [cycle, readiness, exceptions, events, packet, health] = await Promise.all([
        api.cycle(cycleId), api.readiness(cycleId), api.exceptions(cycleId),
        api.events(cycleId), api.packet(cycleId), api.health(),
      ])
      const threads = await Promise.all(exceptions.map((e) => api.thread(e.id, cycleId)))
      const stopped = !!(health as unknown as { run_stopped?: boolean } | null)?.run_stopped
      if (live) { setD({ cycle, readiness, exceptions, events, packet: packet as Data['packet'], threads, stopped, messagingMode: (health as unknown as { adapters?: { messaging?: { mode?: string } } })?.adapters?.messaging?.mode }); setError(null) }
    })().catch((e) => live && setError(e)).finally(() => { if (live) setRefreshing(false) })
    return () => { live = false }
  }, [cycleId, tick])

  useEffect(() => {
    if (api.mode !== 'api' || busy || editing !== null) return
    const t = setInterval(refresh, 4000)
    return () => clearInterval(t)
  }, [refresh, busy, editing])

  useEffect(() => { sessionStorage.setItem(`declined:${cycleId}`, JSON.stringify([...declined])) }, [cycleId, declined])

  async function act(fn: () => Promise<unknown>, msg?: string) {
    setBusy(true); setActErr(null)
    try { await fn(); if (msg) setToast(msg); refresh() } catch (e) { setActErr(e) } finally { setBusy(false) }
  }

  if (error && !d) return <div className="h-page"><div className="h-content"><div className="h-err">Could not load payroll: {maskText(String((error as Error).message ?? error))}</div></div></div>
  if (!d) return <div className="h-page"><div className="h-content"><div className="h-meta">Loading…</div></div></div>

  const idle = !error && !actErr && !acting && editing === null ? idleHomeFor(d, declined) : null
  if (idle) return <BetweenPayrolls data={idle} fakeMessaging={d.messagingMode === 'fake'} />

  const pending = findPending(d, declined)
  const st = steps(d, pending)
  const w = wagesLine(d)
  const s2 = stage2Line(d.readiness.items)
  const rows = activity(d)
  const c = d.cycle
  const circ = 302
  const doneArc = circ - (circ * st.doneCount) / 6
  const curArc = st.cur >= 0 && !st.ready ? circ - circ / 6 : circ
  const started = [...d.events].sort((a, b) => a.at.localeCompare(b.at))[0]?.at
  const needsYou = pending && pending.kind !== 'draft'
  const headline = st.ready ? 'Payroll draft ready for review' : needsYou ? 'One thing needs you.' : pending?.kind === 'draft' ? 'Pilot has questions ready.' : 'Pilot is working on it.'

  return (
    <div className="h-page">
      <header className="h-top">
        <div className="h-logo"><Logo /></div>
        <span className="h-brand">PayrollPilot</span>
        <span className="h-co">{c.company_label}</span>
        <span className="h-grow" />
        <span className="h-test"><i />Test mode · {api.mode === 'fixture' || d.messagingMode === 'fake' ? 'no texts sent' : 'texts go to your phone'}</span>
        <span className="h-badge"><span className="g">G</span>Gusto:<span className="m">not prepared</span></span>
        <button type="button" className="h-pause" disabled={busy || error != null}
          onClick={() => act(() => d.stopped ? api.resume() : api.stop(), d.stopped ? 'Resumed.' : 'Paused. New actions stop; pending approvals stay pending.')}>
          {d.stopped ? 'Resume' : 'Pause'}
        </button>
      </header>

      <main className="h-content">
        {error != null && <div className="h-err" role="alert">Payroll could not refresh. Actions are paused until it reconnects. {maskText(String((error as Error).message ?? error))}</div>}
        {api.mode === 'fixture' || d.messagingMode === 'fake' ? <div className="h-meta" role="status">{api.mode === 'fixture' ? 'Fixture simulation' : 'Fake messaging'} · synthetic data · no texts leave this app.</div> : null}
        {actErr != null && <div className="h-err" role="alert">{maskText(String((actErr as Error).message ?? actErr))}</div>}
        {/* HERO */}
        <section className={`h-card h-hero ${st.ready ? 'ready' : ''}`}>
          <div className="glow" aria-hidden="true" />
          <div className="h-hero-text">
            <div className="row" style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <span className="h-label">{day(c.period_start)} – {day(c.period_end)}{c.payday ? ` · payday ${new Date(`${c.payday}T12:00:00`).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}` : ''}</span>
              {st.ready ? <span className="h-chip green">Ready for review</span> : d.stopped ? <span className="h-chip orange">Paused</span> : null}
            </div>
            {st.ready ? (
              <>
                <div className="h-meta">Employee wages draft</div>
                <Money cents={d.packet?.totals?.stage1_gross_all_cents ?? null} />
              </>
            ) : <h1 className="h-h1">{headline}</h1>}
            <div className="h-lines">
              <div className="h-line"><span className={`d ${w.ok ? 'd-green' : 'd-orange'}`} /><span><strong>Wages</strong> {w.text}</span></div>
              <div className="h-line"><span className={`d ${s2.ok ? 'd-green' : 'd-orange'}`} /><span><strong>Job costs &amp; bonuses</strong> {s2.text}</span></div>
            </div>
          </div>
          <div className="h-ring">
            <div style={{ position: 'relative', width: 112, height: 112 }}>
              <svg aria-hidden="true" width="112" height="112" viewBox="0 0 112 112" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="56" cy="56" r="48" fill="none" stroke="#ECECF1" strokeWidth="10" />
                <circle className="arc" cx="56" cy="56" r="48" fill="none" stroke="#1F8A3B" strokeWidth="10" strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={st.doneCount ? doneArc : circ} />
                <circle className="arc" cx="56" cy="56" r="48" fill="none" stroke="#0A7AFF" strokeWidth="10" strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={curArc}
                  transform={`rotate(${(360 * st.doneCount) / 6} 56 56)`} />
              </svg>
              <div className="in"><div className="n">{st.ready ? <Check s={30} /> : <>{st.cur + 1}<span>/6</span></>}</div>{!st.ready && <div className="u">steps</div>}</div>
            </div>
            <div className="cap">{st.ready ? 'Ready for review' : st.cur >= 0 ? `${SHORT[st.cur]} · step ${st.cur + 1}` : ''}</div>
          </div>
        </section>

        {/* APPROVAL / SUMMARY */}
        {pending?.kind === 'message' && (() => {
          const b = pending.batch
          const roleName = ROLE[b.intended_respondent_role] ?? b.intended_respondent_label
          const isEditing = editing !== null
          return (
            <section className="h-card h-approve" data-batch-id={b.id}>
              <div className="h-ahead">
                <div className="h-avatar"><Logo s={18} /></div>
                <div><div className="h-atitle">Pilot needs your approval</div><div className="h-meta">Message to the {roleName} · {plural(b.exception_ids.length, 'question')}</div></div>
                <span className="h-grow" /><span className="h-chip">Waiting on you</span>
              </div>
              <div className="h-intro">{pending.exceptions.length > 1 ? `${pending.exceptions.length} items need` : 'One item needs'} details that affect payroll. Here's what I'd like to send. Does this look right?</div>
              <div className="h-preview">
                <div className="h-contact"><span className="h-initial">{roleName[0].toUpperCase()}</span>
                  <div><div className="nm">{roleName.replace(/^./, (x) => x.toUpperCase())}</div><div style={{ fontSize: 12 }}>iMessage · <span className="h-mono">{dots(b.actual_recipient)}</span></div></div></div>
                {isEditing
                  ? <textarea className="h-edit" value={editing} onChange={(e) => setEditing(e.target.value)} aria-label="Edit message text" />
                  : <div className="h-bubble">{maskText(b.text)}</div>}
              </div>
              <div className="h-actions">
                {isEditing ? (
                  <>
                    <button type="button" className="h-btn primary" disabled={busy || error != null || !editing?.trim()}
                      onClick={() => act(async () => { await api.editDraft(b.id, editing!, b.text_hash); setEditing(null) }, 'Saved. The new text needs your approval.')}>Save new version</button>
                    <button type="button" className="h-btn tertiary" onClick={() => setEditing(null)}>Cancel</button>
                    <div className="h-note">Any change creates a new version you approve.</div>
                  </>
                ) : (
                  <>
                    <button type="button" className="h-btn primary" disabled={busy || error != null || maskText(b.text) !== b.text}
                      onClick={() => act(async () => {
                        if (!(b.approval_id && b.state === 'approved')) {
                          await api.preflightMessageSend(b)
                          await api.approve({ kind: 'message_send', target_id: b.id, target_version: b.text_hash, scope_text: 'Send this exact text to the allowlisted test recipient' })
                        }
                        await api.send(b.id)
                        setJustSent(b.id)
                      }, `Sent to the ${roleName}.`)}>
                      <Check c="#fff" s={15} />Approve &amp; send
                    </button>
                    <button type="button" className="h-btn secondary" disabled={busy || error != null}

                      onClick={() => setEditing(b.text)}>Edit</button>
                    <button type="button" className="h-btn tertiary" disabled={busy || error != null}
                      onClick={() => act(async () => { await api.declineDraft(b.id, b.text_hash); setDeclined((s) => new Set(s).add(b.id)) }, 'Declined. Nothing was sent.')}>Decline</button>
                    <div className="h-note">{maskText(b.text) !== b.text ? 'This draft contains a phone number. Review it in Details before sending.' : 'Only this text, only to this person.'}</div>
                  </>
                )}
              </div>
            </section>
          )
        })()}

        {pending?.kind === 'correction' && (() => {
          const cr = pending.correction
          const { text, lines } = correctionSentence(cr, pending.exception)
                    return (
            <section className="h-card h-approve">
              <div className="h-ahead">
                <div className="h-avatar"><Logo s={18} /></div>
                <div><div className="h-atitle">Pilot needs your approval</div><div className="h-meta">Correction from the {ROLE[pending.exception.intended_respondent_role] ?? 'respondent'}'s answer</div></div>
                <span className="h-grow" /><span className="h-chip">Waiting on you</span>
              </div>
              <div className="h-intro">{text}</div>
              {lines.length > 0 && <div className="h-impact">{lines.map(([k, v]) => <div key={k}><span>{k}</span><b>{v}</b></div>)}</div>}
              <div className="h-actions">
                <button type="button" className="h-btn primary" disabled={busy || error != null || (!cr.target_version && api.mode === 'api')}
                  onClick={() => act(async () => {
                    const v = cr.target_version ?? await sha256(JSON.stringify({ id: cr.id, kind: cr.kind, before: cr.before, after: cr.after }))
                    await api.approve({ kind: 'local_correction', target_id: cr.id, target_version: v, scope_text: 'Apply this local correction to the PayrollPilot calculation only (no source write)' })
                    await api.applyCorrection(cr.id)
                  }, 'Correction applied. Payroll recalculated.')}>
                  <Check c="#fff" s={15} />Approve &amp; apply
                </button>
                <button type="button" className="h-btn secondary" disabled={busy || error != null} onClick={() => act(() => api.clarify(pending.exception.id), 'Drafted a follow-up for your approval.')}>Ask again</button>
                <div className="h-note">Changes PayrollPilot's numbers only. Jobber, Gusto and QuickBooks are not touched.</div>
              </div>
            </section>
          )
        })()}

        {pending?.kind === 'draft' && (
          <section className="h-card h-approve">
            <div className="h-ahead">
              <div className="h-avatar"><Logo s={18} /></div>
              <div><div className="h-atitle">{plural(pending.exceptions.length, 'question')} for the {ROLE[pending.role]}</div><div className="h-meta">Pilot drafts one message; you approve it before anything is sent</div></div>
            </div>
            <div className="h-rows">
              {pending.exceptions.slice(0, 4).map((e) => <div key={e.id} className="h-row up"><span className="op" /><span className="tx">{e.title}</span></div>)}
              {pending.exceptions.length > 4 && <div className="h-row up"><span className="op" /><span className="tx">and {pending.exceptions.length - 4} more</span></div>}
            </div>
            <div className="h-actions">
              <button type="button" className="h-btn primary" disabled={busy || error != null} onClick={() => act(() => api.draft(pending.exceptions.map((e) => e.id)), 'Drafted. Review the exact text before it is sent.')}>Draft message</button>
              <div className="h-note">Nothing is sent until you approve the exact text.</div>
            </div>
          </section>
        )}

        {justSent && !pending && !st.ready && (
          <section className="h-card h-approve ready"><div className="h-sent"><span className="ok"><Check s={14} /></span>Sent. Pilot will read the reply and come back to you.</div></section>
        )}

        {st.ready && (
          <section className="h-card h-approve ready">
            <div className="h-ahead">
              <div className="h-avatar"><Check c="#fff" s={18} /></div>
              <div><div className="h-atitle">Pilot has a draft for you</div><div className="h-meta">Current review draft · Gusto stays "not prepared"</div></div>
            </div>
            <div className="h-tiles">
              <div className="h-tile"><span className="h-meta">Employee wages</span><span className="v">{formatCents(d.packet?.totals?.stage1_gross_all_cents ?? null)}</span>
                <span className="s">{d.packet?.totals ? `${d.packet.totals.workers_review_ready ?? 0} of ${d.packet.totals.workers_in_cycle ?? 0} verified` : ''}</span></div>
              {(['quote_commission', 'manager_pool'] as const).map((k) => {
                const its = d.readiness.items.filter((i) => i.kind === k || (k === 'quote_commission' && i.kind === 'tip'))
                const open = its.filter((i) => !['ready', 'not_meaningful'].includes(i.readiness.state))
                return <div key={k} className="h-tile"><span className="h-meta">{k === 'quote_commission' ? 'Commissions & tips' : 'Manager pool'}</span>
                  <span className="v">{open.length ? '—' : its.length ? 'Ready' : '—'}</span><span className="s">{open.length ? `${plural(open.length, 'item')} left out` : its.length ? 'verified' : 'none reported'}</span></div>
              })}
            </div>
            <div className="h-rows h-list">
              <div className="h-label" style={{ fontSize: 11.5 }}>Verified</div>
              {(d.packet?.earnings ?? []).filter((e) => e.readiness?.state === 'ready').map((e) => (
                <div key={e.worker_id} className="h-row"><span className="ck"><Check /></span><span className="tx">{e.display_name ?? 'Worker'} <span className="h-meta">· wages verified</span></span><span className="amt">{formatCents(e.gross_new_cents ?? null)}</span></div>
              ))}
            </div>
            {(() => {
              const left = d.readiness.items.filter((i) => i.kind !== 'wages' && !['ready', 'not_meaningful'].includes(i.readiness.state))
              if (!left.length) return null
              return (
                <div className="h-rows">
                  <div className="h-label" style={{ fontSize: 11.5 }}>Left out until you decide</div>
                  {left.map((i) => (
                    <div key={i.id} className="h-row"><span className="op" style={{ borderColor: '#D97A00' }} /><span className="tx">{KIND_NAME[i.kind].replace(/^./, (x) => x.toUpperCase())}{i.job_id ? ` ${i.job_id.replace('job_', 'Job ')}` : ''} <span className="h-meta">· {i.readiness.blockers[0]?.label ?? i.readiness.scope}</span></span>
                      <Link className="h-btn small" to={i.readiness.blockers[0]?.exception_id ? `/e/${i.readiness.blockers[0].exception_id}` : '/details'}>Decide</Link></div>
                  ))}
                </div>
              )
            })()}
            <div className="h-actions">
              <button type="button" className="h-btn primary" disabled title="Internal draft approval is not supported yet">Draft approval unavailable</button>
              <button type="button" className="h-btn secondary" disabled={busy || error != null} onClick={() => act(async () => { const wb = await api.workbook(c.id); setToast(`Review workbook built · ${wb.sheets.length} sheets · original not updated`) })}>Export workbook</button>
              <div className="h-note">Internal draft approval is unavailable. Export is for review; Gusto stays "not prepared".</div>
            </div>
          </section>
        )}

        {/* PROGRESS */}
        <section className="h-card">
          <div className="h-ctitle"><span className="t">Progress</span><span className="h-meta">{st.ready ? 'All 6 steps ready for review' : started ? `Started ${time(started)} today` : 'Waiting to start'}</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div className="h-steps" role="progressbar" aria-valuemin={0} aria-valuemax={6} aria-valuenow={st.doneCount} aria-label={st.ready ? 'All 6 steps ready for review' : `Step ${st.cur + 1} of 6`}>
              {st.done.map((x, i) => (
                <span key={i} style={{ display: 'contents' }}>
                  {i === 4 && <span className="div" aria-hidden="true" />}
                  <span className={`s ${x ? 'done' : i === st.cur ? 'cur' : ''}`} aria-hidden="true" />
                </span>
              ))}
            </div>
            <div className="h-stagelabels">
              <div style={{ flex: '4 1 0' }}><span className="k">Stage 1 · Employee wages</span>
                <span className="sub">{SHORT.slice(0, 4).map((n, i) => <span key={n}>{i ? ' · ' : ''}<span className={i === st.cur ? 'on' : ''}>{n}</span></span>)}</span></div>
              <div style={{ width: 1, flexShrink: 0 }} />
              <div style={{ flex: '2 1 0' }}><span className="k">Stage 2 · Financial reconciliation</span>
                <span className="sub">{SHORT.slice(4).map((n, i) => <span key={n}>{i ? ' · ' : ''}<span className={i + 4 === st.cur ? 'on' : ''}>{n}</span></span>)}</span></div>
            </div>
          </div>
          {st.cur >= 0 && (
            <div className="h-current">
              <div className="dot"><span /></div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3, flex: '1 1 0' }}>
                <div className="ttl">{STEP_NAMES[st.cur]}</div>
                <div className="sub">{currentSub(d, st.cur, pending)}</div>
              </div>
              <div className="now">Now</div>
            </div>
          )}
          <div className="h-rows">
            {!st.ready && STEP_NAMES.map((n, i) => i === st.cur ? null : (
              <div key={n} className={`h-row ${st.done[i] ? '' : 'up'}`}>
                {st.done[i] ? <span className="ck"><Check /></span> : <span className="op" />}
                <span className="tx">{n.replace(/^Gather/, st.done[i] ? 'Gathered' : 'Gather').replace(/^Audit /, st.done[i] ? 'Audited ' : 'Audit ').replace(/^Resolve /, st.done[i] ? 'Resolved ' : 'Resolve ')}</span>
                <span className="tm">{st.done[i] ? time(st.times[i]) : i === st.cur + 1 ? 'next' : ''}</span>
              </div>
            ))}
          </div>
        </section>

        {/* ACTIVITY */}
        <section className="h-card">
          <div className="h-ctitle"><span className="t">What Pilot did today</span><Link to="/details">Details</Link></div>
          <div>
            {rows.length === 0 && <div className="h-meta">Nothing yet.</div>}
            {rows.map((r) => (
              <div key={r.id} className="h-act"><ActIcon k={r.icon} /><div className="tx">{r.text}{r.test && <span className="h-tag">test reply</span>}</div><div className="tm">{time(r.at)}</div></div>
            ))}
          </div>
        </section>

        <footer className="h-foot">
          <span>{api.mode === 'fixture' || d.messagingMode === 'fake' ? 'Test mode: no texts leave this app' : 'Test mode: texts go to your phone'}</span><span aria-hidden="true">·</span>
          <span>{c.provenance === 'real' ? 'Real data (read-only)' : 'Synthetic data'}</span><span aria-hidden="true">·</span>
          <span>Nothing is submitted to Gusto.</span><span aria-hidden="true">·</span>
          <Link to="/details">Details</Link>
        </footer>
      </main>
      {toast && <div className="h-toast" role="status">{toast}<button type="button" onClick={() => setToast(null)}>OK</button></div>}
    </div>
  )
}
