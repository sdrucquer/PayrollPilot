// Display-only helpers. No arithmetic on money beyond formatting integer cents as given.
export const DASH = '—'

export function formatCents(n: number | null | undefined): string {
  if (n === null || n === undefined) return DASH
  const sign = n < 0 ? '-' : ''
  const abs = Math.abs(n)
  const dollars = Math.trunc(abs / 100).toLocaleString('en-US')
  const rem = String(abs % 100).padStart(2, '0')
  return `${sign}$${dollars}.${rem}`
}

export function formatMinutes(n: number | null | undefined): string {
  if (n === null || n === undefined) return DASH
  const h = Math.trunc(n / 60)
  const m = n % 60
  return `${h}h ${String(m).padStart(2, '0')}m`
}

// Mask any recipient or sender handle. Keeps only the last 2 characters.
export function maskHandle(h: string | null | undefined): string {
  if (!h) return DASH
  if (h.includes('*')) return h // already masked by the backend
  const tail = h.replace(/[^0-9A-Za-z]/g, '').slice(-2)
  return `***-**${tail}`
}

export function humanize(s: string): string {
  return s.replace(/[._]/g, ' ')
}

export function formatTime(ts: string | null | undefined): string {
  if (!ts) return DASH
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return ts
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

// Masks phone-number-like sequences inside free text (e.g. an inbound reply that includes a number).
export function maskText(t: string): string {
  // Dates in payroll questions are evidence, not phone handles.
  return t.split(/(\b\d{4}-\d{2}-\d{2}\b)/).map((part) => {
    if (/^\d{4}-\d{2}-\d{2}$/.test(part)) return part
    return part.replace(/(?<![\w$])\+?\d[\d\s().-]{5,}\d/g, (m) => {
      const n = m.replace(/\D/g, '').length
      return n >= 10 || (n === 7 && /[().-]/.test(m)) ? maskHandle(m) : m
    })
  }).join('')
}
