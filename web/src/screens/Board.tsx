import { Link } from 'react-router-dom'
import { api, DEFAULT_CYCLE_ID } from '../api'
import type { PayrollCycle, PayrollException, PPEvent, ReadinessResponse, StageState, Worker } from '../contracts'
import { formatCents, formatTime, humanize } from '../format'
import { useAsync } from '../useAsync'
import { STAGE2, stage2Summary } from '../summary'
import { Card, ErrorBox, Loading, ProvenanceTag, ReadinessBlock, StateTag } from '../components/ui'

function StageHeader({ s }: { s: StageState }) {
  return (
    <div className="stage-head">
      <StateTag value={s.state} kind="stage" />
      <span>{s.scope_note}</span>
      <span className="muted small">unresolved: {s.unresolved_count} · affected: {formatCents(s.dollars_affected_cents)}</span>
    </div>
  )
}

function CycleHeader({ c }: { c: PayrollCycle }) {
  return (
    <section className="cycle-head">
      <div>
        <h2>{c.company_label} <ProvenanceTag value={c.provenance} /></h2>
        <p className="muted">
          Pay period {c.period_start} to {c.period_end} · payday {c.payday ?? '—'} · {c.business_tz} · policy {c.policy_version}
        </p>
      </div>
      <div className="row wrap">
        <span className="kv">Existing run: <StateTag value={c.existing_run_status} kind="run" /></span>
        <span className="kv">Destination: <StateTag value={c.destination} kind="dest" /></span>
      </div>
      <div className="chips">
        {c.coverage.map((cv) => (
          <span key={`${cv.system}-${cv.dataset}`} className={`chip ${cv.complete ? 'chip-ok' : 'chip-bad'}`}
            title={`${cv.range_start} to ${cv.range_end} · snapshot ${cv.snapshot_id}`}>
            {humanize(cv.dataset)} · {cv.complete ? 'full range' : `incomplete: ${humanize(cv.incomplete_reason ?? 'unknown')}`}
            {' '}· {humanize(cv.method)} · {cv.record_count ?? '—'} rec
          </span>
        ))}
      </div>
    </section>
  )
}

function Indicators({ r }: { r: ReadinessResponse }) {
  // CONTRACTS v1 has no fields for labor/revenue review or cash confirmation; they stay at their safe defaults.
  return (
    <div className="indicators">
      <div className="indicator"><span className="muted small">Wage correctness</span><StateTag value={r.stage1.state} kind="ready" /></div>
      <div className="indicator"><span className="muted small">Labor/revenue review</span><span className="tag ready-pending">not reviewed</span></div>
      <div className="indicator"><span className="muted small">Cash confirmation</span><span className="tag ready-blocked">not confirmed</span></div>
    </div>
  )
}

export default function Board() {
  const cycleId = DEFAULT_CYCLE_ID
  const { data, error, loading } = useAsync(
    () => Promise.all([
      api.cycle(cycleId), api.readiness(cycleId), api.workers(cycleId),
      api.exceptions(cycleId).catch(() => [] as PayrollException[]),
      api.events(cycleId).catch(() => [] as PPEvent[]),
    ]),
    [cycleId],
  )
  if (loading && !data) return <Loading />
  if (error) return <ErrorBox error={error} />
  if (!data) return null
  const [cycle, readiness, workers, exceptions, events] = data
  const open = exceptions.filter((e) => e.state !== 'resolved')
  const names = new Map<string, Worker>(workers.map((w) => [w.id, w]))
  const wages = readiness.items.filter((i) => i.kind === 'wages')
  const stage2Items = readiness.items.filter((i) => i.kind !== 'wages')

  return (
    <div className="stack">
      <CycleHeader c={cycle} />
      <Indicators r={readiness} />

      <div className="grid-2">
        <Card title={`Needs attention · ${open.length}`} right={<Link to="/inbox">Open inbox</Link>}>
          {open.length === 0 && <p className="muted">No open exceptions reported.</p>}
          {open.slice(0, 6).map((e) => (
            <div key={e.id} className="exc-row">
              <div>
                <Link to={`/inbox/${e.id}`}>{e.title}</Link>
                <div className="muted small">{humanize(e.category)} · ask {humanize(e.intended_respondent_role)} · {e.next_action}</div>
              </div>
              <div className="row wrap" style={{ justifyContent: 'flex-end' }}>
                <StateTag value={e.state} kind="exc" />
                <span className="small">{formatCents(e.dollars_affected_cents)}</span>
                <ProvenanceTag value={e.provenance} />
              </div>
            </div>
          ))}
        </Card>
        <Card title="Agent activity" right={<Link to="/activity">All events</Link>}>
          {events.length === 0 && <p className="muted">No events yet.</p>}
          <ul className="feed">
            {events.slice(-6).reverse().map((ev) => (
              <li key={ev.id}>
                <span className={`actor actor-${ev.actor}`}>{ev.actor}</span>
                <span className="muted small feed-type">{ev.type}</span>
                <span>{ev.summary} <span className="tiny">{formatTime(ev.at)}</span></span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card title="Stage 1 · Wages" right={<ProvenanceTag value={cycle.provenance} />}>
        <StageHeader s={cycle.stage1} />
        <ReadinessBlock r={readiness.stage1} />
        <table className="table">
          <thead><tr><th>Worker</th><th>Identity</th><th>Readiness</th><th>Scope</th><th>Blockers</th><th>Provenance</th></tr></thead>
          <tbody>
            {wages.map((i) => {
              const w = i.worker_id ? names.get(i.worker_id) : undefined
              return (
                <tr key={i.id}>
                  <td>{w?.display_name ?? i.worker_id ?? '—'}</td>
                  <td>{w ? humanize(w.identity_status) : '—'}</td>
                  <td><StateTag value={i.readiness.state} kind="ready" /></td>
                  <td>{i.readiness.scope}</td>
                  <td>{i.readiness.blockers.length === 0 ? '—' : i.readiness.blockers.map((b) => (
                    <div key={b.code}><code>{b.code}</code> {b.label}</div>
                  ))}</td>
                  <td><ProvenanceTag value={i.provenance} /></td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </Card>

      <section>
        <h3 className="section-title">Stage 2</h3>
        <StageHeader s={cycle.stage2} />
        <p className="summary-line"><strong>Summary:</strong> {stage2Summary(stage2Items)}</p>
        <div className="grid">
          {STAGE2.map(({ kind, title }) => {
            const items = stage2Items.filter((i) => i.kind === kind)
            if (kind === 'marketing' && items.length === 0) return null
            return (
              <Card key={kind} title={title}>
                {items.length === 0 && <p className="muted">No item reported by the backend.</p>}
                {items.map((i) => (
                  <div key={i.id} className="item">
                    <div className="row wrap small">
                      <span className="muted">{i.id}</span>
                      {i.job_id && <span>job {i.job_id}</span>}
                      {i.worker_id && <span>{names.get(i.worker_id)?.display_name ?? i.worker_id}</span>}
                      <ProvenanceTag value={i.provenance} />
                    </div>
                    <ReadinessBlock r={i.readiness} />
                  </div>
                ))}
              </Card>
            )
          })}
        </div>
      </section>
    </div>
  )
}
