import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, DEFAULT_CYCLE_ID } from '../api'
import type { PayrollException } from '../contracts'
import { formatCents, humanize } from '../format'
import { useAsync } from '../useAsync'
import { ErrorBox, Loading, ProvenanceTag, StateTag } from '../components/ui'
import Thread from './Thread'

const GROUPS: { key: string; label: string; test: (e: PayrollException) => boolean }[] = [
  { key: 'all', label: 'All', test: () => true },
  { key: 'wages', label: 'Wages', test: (e) => e.stage_impact.stage1_wages !== 'none' },
  { key: 'costs', label: 'Costs', test: (e) => e.stage_impact.stage2_costs === 'job_costing' },
  { key: 'commissions', label: 'Commissions', test: (e) => ['commission', 'manager_pool'].includes(e.stage_impact.stage2_costs) },
  { key: 'prior', label: 'Prior payment', test: (e) => ['already_paid_allocation', 'unassigned_time'].includes(e.category) },
  { key: 'policy', label: 'Policy', test: (e) => ['policy_missing', 'coverage_gap'].includes(e.category) },
]

function impact(e: PayrollException): string {
  const parts = []
  if (e.stage_impact.stage1_wages !== 'none') parts.push(`wages: ${humanize(e.stage_impact.stage1_wages)}`)
  if (e.stage_impact.stage2_costs !== 'none') parts.push(humanize(e.stage_impact.stage2_costs))
  return parts.join(' · ') || 'no stage impact'
}

export default function Inbox() {
  const { id } = useParams()
  const [group, setGroup] = useState('all')
  const [state, setState] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [tick, setTick] = useState(0)
  const [err, setErr] = useState<unknown>(null)
  const { data, error, loading } = useAsync(() => api.exceptions(DEFAULT_CYCLE_ID), [tick])
  const list = useMemo(() => {
    const g = GROUPS.find((x) => x.key === group)!
    return (data ?? []).filter((e) => g.test(e) && (!state || e.state === state))
  }, [data, group, state])
  const states = [...new Set((data ?? []).map((e) => e.state))]

  async function draftSelected() {
    setErr(null)
    try { await api.draft(selected); setSelected([]); setTick((t) => t + 1) } catch (e) { setErr(e) }
  }
  const sameRole = selected.length > 0 && new Set((data ?? []).filter((e) => selected.includes(e.id)).map((e) => e.intended_respondent_role)).size === 1

  return (
    <div className={`inbox ${id ? 'has-thread' : ''}`}>
      <section className="inbox-list">
        <div className="filters">
          {GROUPS.map((g) => (
            <button key={g.key} className={`pill ${group === g.key ? 'on' : ''}`} onClick={() => setGroup(g.key)}>{g.label}</button>
          ))}
          <select value={state} onChange={(e) => setState(e.target.value)} aria-label="Filter by state">
            <option value="">Any state</option>
            {states.map((s) => <option key={s} value={s}>{humanize(s)}</option>)}
          </select>
        </div>
        {selected.length > 0 && (
          <div className="batchbar">
            <span>{selected.length} selected</span>
            <button className="btn primary" disabled={!sameRole} onClick={draftSelected}
              title={sameRole ? '' : 'A batch goes to one respondent role'}>Draft one grouped question</button>
            {!sameRole && <span className="muted small">Pick issues for the same respondent role.</span>}
          </div>
        )}
        {err != null && <ErrorBox error={err} />}
        {loading && !data && <Loading />}
        {error != null && <ErrorBox error={error} />}
        <ul className="exc-list">
          {list.map((e) => (
            <li key={e.id} className={e.id === id ? 'active' : ''}>
              <input type="checkbox" aria-label={`select ${e.id}`} checked={selected.includes(e.id)}
                onChange={(ev) => setSelected((s) => ev.target.checked ? [...s, e.id] : s.filter((x) => x !== e.id))} />
              <Link to={`/inbox/${e.id}`} className="exc-link">
                <div className="exc-title">{e.title}</div>
                <div className="muted small">{humanize(e.category)} · {impact(e)} · ask {humanize(e.intended_respondent_role)}</div>
                <div className="muted small">Next: {e.next_action}</div>
                <div className="row wrap">
                  <StateTag value={e.state} kind="exc" />
                  <span className="small">{formatCents(e.dollars_affected_cents)}</span>
                  <ProvenanceTag value={e.provenance} />
                </div>
              </Link>
            </li>
          ))}
          {data && list.length === 0 && <li className="muted">No exceptions match.</li>}
        </ul>
      </section>
      {id ? <Thread key={id} id={id} onChange={() => setTick((t) => t + 1)} /> : (
        <section className="thread empty muted">Select an exception to see its evidence and conversation.</section>
      )}
    </div>
  )
}
