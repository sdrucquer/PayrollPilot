import { useEffect, useRef } from 'react'
import { maskHandle } from '../format'

export interface ApprovalRequest {
  title: string
  kind: 'message_send' | 'local_correction'
  targetId: string
  targetVersion: string
  scopeText: string
  text?: string
  recipient?: string
  recipientRole?: string
  exceptionIds: string[]
  details?: React.ReactNode
  confirmLabel: string
}

export default function ApprovalDialog({ req, busy, onConfirm, onCancel, onSecondary, secondaryLabel }: {
  req: ApprovalRequest; busy: boolean; onConfirm: () => void; onCancel: () => void
  onSecondary?: () => void; secondaryLabel?: string
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { ref.current?.showModal() }, [])
  return (
    <dialog ref={ref} className="dialog" onCancel={(e) => { e.preventDefault(); onCancel() }}>
      <h3>{req.title}</h3>
      <p className="muted small">Owner approval binds to this exact version. Any change requires a new approval.</p>
      {req.text !== undefined && (
        <>
          <div className="label">Exact text</div>
          <pre className="msg-text">{req.text}</pre>
        </>
      )}
      {req.recipient !== undefined && (
        <div className="kvs">
          <div><span className="label">Recipient</span>{maskHandle(req.recipient)} <span className="muted small">(allowlisted test handle)</span></div>
          <div><span className="label">Intended respondent</span>{req.recipientRole}</div>
        </div>
      )}
      {req.details}
      <div className="kvs">
        <div><span className="label">Linked issues</span>{req.exceptionIds.join(', ')}</div>
        <div><span className="label">Target</span><code>{req.targetId}</code></div>
        <div><span className="label">Version</span><code>{req.targetVersion.slice(0, 23)}…</code></div>
        <div><span className="label">Scope</span>{req.scopeText}</div>
      </div>
      <div className="row actions">
        <button className="btn" onClick={onCancel} disabled={busy}>Cancel</button>
        {onSecondary && <button className="btn" onClick={onSecondary} disabled={busy}>{secondaryLabel}</button>}
        <button className="btn primary" onClick={onConfirm} disabled={busy}>{busy ? 'Working…' : req.confirmLabel}</button>
      </div>
    </dialog>
  )
}
