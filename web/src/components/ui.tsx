import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'
import type { Blocker, Provenance, Readiness } from '../contracts'
import { humanize } from '../format'

export function ProvenanceTag({ value }: { value: Provenance }) {
  return <span className={`tag prov prov-${value}`} title="provenance">{humanize(value)}</span>
}

export function StateTag({ value, kind = 'state' }: { value: string; kind?: string }) {
  return <span className={`tag ${kind}-${value}`}>{humanize(value)}</span>
}

export function BlockerList({ blockers }: { blockers: Blocker[] }) {
  if (blockers.length === 0) return <p className="muted small">No blockers reported.</p>
  return (
    <ul className="blockers">
      {blockers.map((b) => (
        <li key={`${b.code}-${b.exception_id ?? ''}`}>
          <code>{b.code}</code> {b.label}
          {b.exception_id && <> · <Link to={`/inbox/${b.exception_id}`}>{b.exception_id}</Link></>}
        </li>
      ))}
    </ul>
  )
}

export function ReadinessBlock({ r }: { r: Readiness }) {
  return (
    <div className="readiness">
      <div className="row">
        <StateTag value={r.state} kind="ready" />
        <span className="scope">{r.scope}</span>
      </div>
      {r.unknown_amount && <p className="warn small">Amount unknown until blockers clear.</p>}
      <BlockerList blockers={r.blockers} />
      <p className="muted tiny">{r.calculation_version} · computed {new Date(r.last_computed_at).toLocaleTimeString()}</p>
    </div>
  )
}

export function Card({ title, right, children }: { title: ReactNode; right?: ReactNode; children: ReactNode }) {
  return (
    <section className="card">
      <header className="card-head"><h3>{title}</h3><div className="row">{right}</div></header>
      {children}
    </section>
  )
}

export function Loading() { return <p className="muted">Loading…</p> }

export function ErrorBox({ error }: { error: unknown }) {
  return <div className="error"><strong>Error:</strong> {error instanceof Error ? error.message : String(error)}</div>
}
