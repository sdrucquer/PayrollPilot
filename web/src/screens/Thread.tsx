import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, DEFAULT_CYCLE_ID, type Thread as ThreadData } from '../api'
import type { LocalCorrection, MessageBatch, PayrollException } from '../contracts'
import { formatCents, formatTime, humanize, maskHandle, maskText } from '../format'
import { sha256 } from '../sim'
import { useAsync } from '../useAsync'
import { ErrorBox, Loading, ProvenanceTag, StateTag } from '../components/ui'
import ApprovalDialog, { type ApprovalRequest } from '../components/ApprovalDialog'

const CORRECTION_KIND: Partial<Record<PayrollException['category'], LocalCorrection['kind']>> = {
  missing_job: 'job_allocation', already_paid_allocation: 'job_allocation', unassigned_time: 'job_allocation',
  rate_unconfirmed: 'rate_confirmation', unmatched_cost: 'cost_link', cost_conflict: 'cost_link', offsite_link: 'cost_link',
  identity: 'identity_merge',
}

function Facts({ obj }: { obj: Record<string, unknown> }) {
  const entries = Object.entries(obj)
  if (entries.length === 0) return <span className="muted">—</span>
  return (
    <span className="facts">
      {entries.map(([k, v]) => (
        <span key={k}><span className="muted">{humanize(k)}:</span> {k.endsWith('_cents') ? formatCents(v as number | null) : v === null ? '—' : typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
      ))}
    </span>
  )
}

function Impact({ impact }: { impact: Record<string, unknown> }) {
  const wages = impact.stage1_wages_delta_cents as number | null | undefined
  const jobs = (impact.job_costing_delta ?? []) as { job_id: string; labor_delta_cents: number | null }[]
  if (wages === undefined && jobs.length === 0) return <p className="muted small">Calculation impact not provided.</p>
  return (
    <table className="table compact">
      <tbody>
        {wages !== undefined && <tr><td>Stage 1 wages change</td><td className="num">{formatCents(wages)}</td></tr>}
        {jobs.map((j) => <tr key={j.job_id}><td>{j.job_id} labor cost change</td><td className="num">{formatCents(j.labor_delta_cents)}</td></tr>)}
      </tbody>
    </table>
  )
}

export default function Thread({ id, onChange }: { id: string; onChange: () => void }) {
  const [tick, setTick] = useState(0)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<unknown>(null)
  const [dialog, setDialog] = useState<(ApprovalRequest & { run: () => Promise<unknown>; approveOnly?: () => Promise<unknown> }) | null>(null)
  const [editing, setEditing] = useState<{ batch: string; text: string } | null>(null)
  const { data, error, loading } = useAsync(() => api.thread(id, DEFAULT_CYCLE_ID), [id, tick])

  async function act(fn: () => Promise<unknown>) {
    setBusy(true); setErr(null)
    try { await fn(); setTick((t) => t + 1); onChange() } catch (e) { setErr(e) } finally { setBusy(false) }
  }

  if (loading && !data) return <section className="thread"><Loading /></section>
  if (error) return <section className="thread"><ErrorBox error={error} /></section>
  if (!data) return null
  const t: ThreadData = data
  const e = t.exception
  const approvalFor = (b: MessageBatch) => t.approvals.find((a) => a.id === b.approval_id)
  const invalidated = (b: MessageBatch) => t.approvals.filter((a) => a.target_id === b.id && a.state === 'invalidated')
  const hasOpenDraft = t.batches.some((b) => b.state === 'draft' || b.state === 'approved')
  const needsClarify = t.parsed.some((p) => p.needs_clarification.includes(e.id)
    || p.answers.some((a) => a.exception_id === e.id && ['ambiguous', 'partial', 'conflicting'].includes(a.status)))

  function openSend(b: MessageBatch) {
    const a = approvalFor(b)
    const valid = a && a.state === 'active' && a.target_version === b.text_hash
    setDialog({
      title: valid ? 'Send approved message' : 'Approve and send this message',
      kind: 'message_send', targetId: b.id, targetVersion: b.text_hash,
      scopeText: 'Send this exact text to the allowlisted test recipient', text: b.text,
      recipient: b.actual_recipient, recipientRole: b.intended_respondent_label, exceptionIds: b.exception_ids,
      confirmLabel: valid ? 'Send' : 'Approve + Send',
      approveOnly: valid ? undefined : () => api.approve({ kind: 'message_send', target_id: b.id, target_version: b.text_hash, scope_text: 'Send this exact text to the allowlisted test recipient' }),
      run: async () => {
        if (!valid) await api.approve({ kind: 'message_send', target_id: b.id, target_version: b.text_hash, scope_text: 'Send this exact text to the allowlisted test recipient' })
        await api.send(b.id)
      },
    })
  }

  async function openCorrectionApproval(c: LocalCorrection) {
    // Backend (A-04) puts target_version on the correction; fixture mode hashes the proposal.
    const version = (c as LocalCorrection & { target_version?: string }).target_version
      ?? await sha256(JSON.stringify({ id: c.id, kind: c.kind, before: c.before, after: c.after }))
    setDialog({
      title: 'Approve local correction', kind: 'local_correction', targetId: c.id, targetVersion: version,
      scopeText: 'Apply this local correction to the PayrollPilot calculation only (no source write)',
      exceptionIds: [e.id], confirmLabel: 'Approve correction',
      details: (
        <div className="kvs">
          <div><span className="label">Before</span><Facts obj={c.before} /></div>
          <div><span className="label">After</span><Facts obj={c.after} /></div>
          <Impact impact={c.calculation_impact} />
        </div>
      ),
      run: () => api.approve({ kind: 'local_correction', target_id: c.id, target_version: version, scope_text: 'Apply this local correction to the PayrollPilot calculation only (no source write)' }),
    })
  }

  return (
    <section className="thread">
      <header className="thread-head">
        <Link to="/" className="back small">All blockers</Link>
        <div className="row wrap">
          <StateTag value={e.state} kind="exc" />
          <span className="muted small">{humanize(e.category)}</span>
          <ProvenanceTag value={e.provenance} />
          <span className="muted small">owner agent: {e.owner_agent}</span>
        </div>
        <h2>{e.title}</h2>
        <p className="muted small">Ask: {humanize(e.intended_respondent_role)} · Next: {e.next_action} · {e.id}</p>
      </header>

      <div className="ovse">
        <div><div className="label">Observed</div><p>{e.observed}</p></div>
        <div><div className="label">Expected</div><p>{e.expected}</p></div>
      </div>

      <div className="kvs">
        <div><span className="label">Stage impact</span>wages {humanize(e.stage_impact.stage1_wages)} · stage 2 {humanize(e.stage_impact.stage2_costs)}</div>
        <div><span className="label">Dollars affected</span>{formatCents(e.dollars_affected_cents)}</div>
        <div><span className="label">Entities</span>
          <Facts obj={Object.fromEntries(Object.entries(e.entity_refs).filter(([, v]) => v !== null && !(Array.isArray(v) && v.length === 0)).map(([k, v]) => [k, Array.isArray(v) ? v.join(', ') : v]))} />
        </div>
        <div><span className="label">Evidence</span>
          {e.evidence.length === 0 ? <span className="muted">No source refs attached in this fixture.</span> : (
            <span className="facts">{e.evidence.map((r) => (
              <span key={r.system + r.record_id}>
                {r.system} <code>{r.record_id}</code>{r.url && <> · <a href={r.url} target="_blank" rel="noreferrer">open</a></>} <span className="muted tiny">{r.snapshot_id}</span>
              </span>
            ))}</span>
          )}
        </div>
      </div>

      <h3 className="section-title">Conversation</h3>
      {t.batches.length === 0 && <p className="muted small">No question drafted yet.</p>}
      <div className="convo">
        {t.batches.map((b) => {
          const a = approvalFor(b)
          const stale = a && a.target_version !== b.text_hash
          const replies = t.inbound.filter((m) => m.correlated_batch_id === b.id)
          return (
            <div key={b.id} className="convo-group">
              <div className="bubble out">
                <div className="row wrap small">
                  <span className="actor actor-resolution">Resolution agent</span>
                  <span className="muted">to {b.intended_respondent_label} · {maskHandle(b.actual_recipient)} · iMessage</span>
                  <StateTag value={b.state} kind="msg" />
                  {b.exception_ids.length > 1 && <span className="muted">{b.exception_ids.length} questions</span>}
                </div>
                {editing?.batch === b.id ? (
                  <textarea className="edit" value={editing.text} onChange={(ev) => setEditing({ batch: b.id, text: ev.target.value })} />
                ) : <p className="msg-body">{b.text}</p>}
                <div className="muted tiny">
                  {b.sent_at ? `sent ${formatTime(b.sent_at)}` : 'not sent'}{b.provider_status && ` · ${b.provider_status}`} · {b.text_hash.slice(0, 15)}…
                </div>
                {invalidated(b).length > 0 && b.state !== 'sent' && (
                  <p className="warn small">Earlier approval invalidated: {invalidated(b)[0].invalidated_reason ?? 'text changed'}. Re-approval required.</p>
                )}
                {stale && <p className="warn small">Text changed since approval. Re-approval required.</p>}
                {b.state !== 'sent' && b.state !== 'delivered' && (
                  <div className="row wrap actions">
                    {editing?.batch === b.id ? (
                      <>
                        <button className="btn" disabled={busy} onClick={() => setEditing(null)}>Cancel</button>
                        <button className="btn" disabled={busy} onClick={() => act(async () => { await api.editDraft(b.id, editing.text); setEditing(null) })}>Save text</button>
                      </>
                    ) : (
                      <>
                        {api.mode === 'fixture' && <button className="btn" disabled={busy} onClick={() => setEditing({ batch: b.id, text: b.text })}>Edit text</button>}
                        <button className="btn primary" disabled={busy} onClick={() => openSend(b)}>
                          {a && a.state === 'active' && !stale ? 'Send' : 'Approve + Send'}
                        </button>
                      </>
                    )}
                  </div>
                )}
                {b.state === 'sent' && replies.length === 0 && api.mode === 'fixture' && (
                  <div className="row actions">
                    <button className="btn" disabled={busy} onClick={() => act(() => api.simulateReply(b.id))}>Simulate test reply (fixture)</button>
                  </div>
                )}
              </div>
              {replies.map((m) => {
                const p = t.parsed.find((x) => x.inbound_id === m.id)
                const blocked = t.blockedInboundIds.includes(m.id)
                return (
                  <div key={m.id} className="bubble in">
                    <div className="row wrap small">
                      <span className="actor actor-owner">Reply</span>
                      <span className="muted">from {maskHandle(m.sender)} · {formatTime(m.received_at)}</span>
                      <ProvenanceTag value={m.provenance} />
                      {blocked && <span className="tag ready-blocked">Blocked instruction</span>}
                    </div>
                    <p className="msg-body">{maskText(m.raw_text)}</p>
                    {blocked && <p className="bad small">This reply contained instructions. They were treated as data and not acted on.</p>}
                    {p && (
                      <div className="parsed">
                        <div className="label">Parsed answers <span className="muted tiny">{p.model}</span></div>
                        {p.answers.map((ans) => (
                          <div key={ans.exception_id} className={`answer ${ans.exception_id === e.id ? 'this' : ''}`}>
                            <StateTag value={ans.status} kind="ans" />
                            <code>{ans.exception_id}</code>
                            <Facts obj={ans.extracted} />
                            <span className="muted tiny">confidence {ans.confidence.toFixed(2)}</span>
                          </div>
                        ))}
                        {p.needs_clarification.length > 0 && <p className="warn small">Needs clarification: {p.needs_clarification.join(', ')}</p>}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>

      {t.resolution && (
        <>
          <h3 className="section-title">Resolution</h3>
          <div className="kvs">
            <div><span className="label">Confirmed facts</span><Facts obj={t.resolution.confirmed_facts} /></div>
            <div><span className="label">Confirmed by</span>{humanize(t.resolution.confirmer_actual)} for {humanize(t.resolution.confirmer_intended_role)}</div>
          </div>
        </>
      )}

      {t.correction && (
        <>
          <h3 className="section-title">Local correction</h3>
          <div className="kvs">
            <div><span className="label">Kind</span>{humanize(t.correction.kind)} <StateTag value={t.correction.state} kind="corr" /></div>
            <div><span className="label">Before</span><Facts obj={t.correction.before} /></div>
            <div><span className="label">After</span><Facts obj={t.correction.after} /></div>
            <Impact impact={t.correction.calculation_impact} />
            <p className="muted tiny">Local to PayrollPilot. Source systems are read-only; source writes are unavailable.</p>
          </div>
        </>
      )}

      {err != null && <ErrorBox error={err} />}
      <div className="row wrap actions sticky-actions">
        {e.intended_respondent_role === 'owner' && e.state !== 'resolved' && (
          <p className="muted small">This is your decision, not a question to send. Next: {e.next_action}.</p>
        )}
        {!hasOpenDraft && e.state !== 'resolved' && !needsClarify && e.intended_respondent_role !== 'owner' && (
          <button className="btn primary" disabled={busy} onClick={() => act(() => api.draft([e.id]))}>Draft question</button>
        )}
        {needsClarify && e.state !== 'resolved' && !hasOpenDraft && (
          <button className="btn primary" disabled={busy} onClick={() => act(() => api.clarify(e.id))}>Clarify</button>
        )}
        {t.resolution && !t.correction && (
          <button className="btn primary" disabled={busy}
            onClick={() => act(() => api.proposeCorrection(t.resolution!.id, CORRECTION_KIND[e.category] ?? 'time_confirmation', t.resolution!.confirmed_facts))}>
            Propose correction
          </button>
        )}
        {t.correction?.state === 'proposed' && (
          <button className="btn primary" disabled={busy} onClick={() => openCorrectionApproval(t.correction!)}>Approve correction</button>
        )}
        {t.correction?.state === 'approved' && (
          <button className="btn primary" disabled={busy} onClick={() => act(() => api.applyCorrection(t.correction!.id))}>Apply correction</button>
        )}
        {api.mode === 'api' && e.owner_agent === 'audit' && (
          <button className="btn" disabled={busy} onClick={() => act(() => api.handoff(e.id))}>Hand off to Resolution</button>
        )}
        <button className="btn" disabled title="Gated: no executor in this pilot">Write to source (unavailable)</button>
      </div>

      {dialog && (
        <ApprovalDialog req={dialog} busy={busy}
          onCancel={() => setDialog(null)}
          onConfirm={() => act(async () => { await dialog.run(); setDialog(null) })}
          onSecondary={dialog.approveOnly && (() => act(async () => { await dialog.approveOnly!(); setDialog(null) }))}
          secondaryLabel="Approve only" />
      )}
    </section>
  )
}
