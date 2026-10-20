import { Link } from 'react-router-dom'
import { formatCents, maskText } from '../format'
import { workbookDownloadUrl, type IdleHome } from '../idle-state'
import '../idle.css'

function Check({ size = 12, strokeWidth = 2.4 }: { size?: number; strokeWidth?: number }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="#1F8A3B" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"><path d="M3 8.5l3.5 3.5 7-8" /></svg>
}
function RecentIcon({ kind }: { kind: IdleHome['recent'][number]['icon'] }) {
  if (kind === 'check') return <span className="i-icon green"><Check size={14} strokeWidth={2} /></span>
  return <span className={`i-icon ${kind === 'clock' ? 'blue' : 'gray'}`}><svg aria-hidden="true" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke={kind === 'clock' ? '#0066D6' : '#3A3A3C'} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{kind === 'clock' ? <><circle cx="8" cy="8" r="5.5" /><path d="M8 5v3.5l2 1.5" /></> : <><rect x="3" y="2.5" width="10" height="11" rx="1.5" /><path d="M5.5 6h5M5.5 9h5" /></>}</svg></span>
}

export default function BetweenPayrolls({ data, preview = false, fakeMessaging = false }: { data: IdleHome; preview?: boolean; fakeMessaging?: boolean }) {
  const text = (value: string) => maskText(value)
  const money = formatCents(data.last.gross_cents).split('.')
  const workbook = workbookDownloadUrl(data.last.workbook_url)
  return <>
    {preview && <aside className="i-preview" role="status">Design preview · Synthetic scenario · No live actions <Link to="/">Return to current payroll</Link></aside>}
    <div className="i-page">
      <header className="i-top">
        <div className="i-brand"><span className="i-logo"><svg aria-hidden="true" width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12.5 8 3l5 9.5" /><path d="M5.5 9.5h5" /></svg></span><strong>PayrollPilot</strong><span className="i-company">{text(data.company_label)}</span></div>
        <span className="i-grow" />
        <span className="i-test"><i />Test mode · {fakeMessaging ? 'no texts sent' : 'texts go to your phone'}</span>
        <span className="i-destination"><span>G</span>Gusto:<b>not prepared</b></span>
      </header>
      <main className="i-content">
        <section className="i-card i-hero">
          <div className="i-glow" aria-hidden="true" />
          <div className="i-hero-copy">
            <div className="i-label">Next payroll · {text(data.next.period_label)} · payday {text(data.next.payday_label)}</div>
            <h1>Next payroll starts {text(data.next.starts_label)}.</h1>
            <div className="i-description">{text(data.next.summary)}</div>
            <div className="i-actions"><button className="i-button secondary" disabled title="Starting early is unavailable; no schedule will change">Start early</button><button className="i-button tertiary" disabled title="Schedule changes are unavailable">Change schedule</button></div>
            {!preview && <div className="i-meta">Scheduling controls are unavailable.</div>}
          </div>
          <div className="i-ring" role="img" aria-label={`${data.next.days_until_start} days until next payroll starts`}>
            <div className="i-ring-circle"><svg aria-hidden="true" width="112" height="112" viewBox="0 0 112 112"><circle cx="56" cy="56" r="48" fill="none" stroke="#ECECF1" strokeWidth="10" /></svg><div className="i-ring-inside"><b>{data.next.days_until_start}</b><span>{data.next.days_until_start === 1 ? 'day' : 'days'}</span></div></div><span className="i-caption">until it starts</span>
          </div>
        </section>
        <section className="i-card i-last">
          <div className="i-card-head"><h2>Last payroll</h2><span className="i-meta">{text(data.last.period_label)}</span><span className="i-grow" />{workbook && !preview ? <a href={workbook} download>Download workbook</a> : <button className="i-link" disabled title="Workbook download unavailable">Download workbook</button>}</div>
          <div className="i-last-total"><div className="i-money">{money[0]}{money[1] && <span>.{money[1]}</span>}</div><div className="i-last-summary">{text(data.last.summary)}</div></div>
          <div className="i-badges">{data.last.approved_label && <span className="i-status green"><Check />{text(data.last.approved_label)}</span>}{data.last.submitted_label && <span className="i-status green"><Check />{text(data.last.submitted_label)}</span>}{data.last.waiting_label && <span className="i-status orange">{text(data.last.waiting_label)}</span>}</div>
          {!preview && !workbook && <div className="i-meta">Workbook download unavailable.</div>}
        </section>
        <section className="i-card i-connections"><h2>Connected, read only</h2><div className="i-connection-grid">{data.connections.map((c) => <div key={c.system} className="i-connection"><span aria-hidden="true" className={`i-system ${c.system}`}>{c.system === 'jobber' ? 'J' : c.system === 'quickbooks' ? 'Q' : 'G'}</span><div><div className="i-connection-name">{text(c.label)}</div><div className="i-connection-status"><i className={c.verified ? 'verified' : 'partial'} />{text(c.status)}</div></div></div>)}</div></section>
        <section className="i-card i-recent"><div className="i-card-head"><h2>Recent</h2><span className="i-grow" /><Link to="/details">Details</Link></div><div>{data.recent.map((r) => <div key={r.id} className="i-activity"><RecentIcon kind={r.icon} /><span className="i-activity-text">{text(r.text)}</span><span className="i-date">{text(r.date_label)}</span></div>)}</div></section>
        <footer className="i-footer"><span>Test mode: {fakeMessaging ? 'no texts leave this app' : 'texts go to your phone'}</span><span aria-hidden="true">·</span><span>{data.provenance === 'synthetic' ? 'Synthetic data' : 'Real data (read-only)'}</span><span aria-hidden="true">·</span><span>Nothing is submitted to Gusto.</span></footer>
      </main>
    </div>

  </>
}
