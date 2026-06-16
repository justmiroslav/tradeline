const LOCALE = "en-US"

export function formatPrice(cents: number): string {
  if (cents === 0) return "$0"
  return `$${(cents / 100).toFixed(2)}`
}

export function formatDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString(LOCALE, { year: "numeric", month: "short", day: "numeric" })
}

export function formatDateTime(iso: string, opts: { seconds?: boolean } = {}): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString(LOCALE, {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
    ...(opts.seconds ? { second: "2-digit" } : {})
  })
}

export function formatDateCompact(d: Date): string {
  if (isNaN(d.getTime())) return ""
  return d.toLocaleDateString(LOCALE, { month: "short", day: "numeric" })
}

function ymdParts(ymd: string): [number, number, number] | null {
  const [y, m, d] = ymd.split("-").map(Number)
  if (!y || !m || !d) return null
  return [y, m, d]
}

export function formatDayLabel(ymd: string): string {
  const p = ymdParts(ymd)
  if (!p) return ymd
  return new Date(p[0], p[1] - 1, p[2]).toLocaleDateString(LOCALE, { month: "short", day: "numeric" })
}

export function formatDayFull(ymd: string): string {
  const p = ymdParts(ymd)
  if (!p) return ymd
  return new Date(p[0], p[1] - 1, p[2]).toLocaleDateString(LOCALE, { year: "numeric", month: "short", day: "numeric" })
}

export function formatDateTimeShort(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString(LOCALE, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false })
}

export function formatNumber(n: number, opts?: Intl.NumberFormatOptions): string {
  return n.toLocaleString(LOCALE, opts)
}

export function formatAmount(n: number | null): string {
  if (n == null) return "—"
  return formatNumber(n, { maximumFractionDigits: Math.abs(n) >= 1000 ? 2 : 6 })
}

export function formatPercent(n: number | null): string {
  if (n == null) return "—"
  return `${formatNumber(n * 100, { maximumFractionDigits: 1 })}%`
}

export function formatSignedUsd(n: number): string {
  const sign = n > 0 ? "+" : n < 0 ? "-" : ""
  return `${sign}$${formatNumber(Math.abs(n), { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function formatCompactUsd(n: number): string {
  const a = Math.abs(n)
  const sign = n < 0 ? "-" : ""
  if (a >= 1000) return `${sign}$${formatNumber(a / 1000, { maximumFractionDigits: a >= 10000 ? 0 : 1 })}k`
  return `${sign}$${formatNumber(a, { maximumFractionDigits: 0 })}`
}

export function humanizeLabel(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, " ")
}

export function parseDecimal(value: string | null | undefined): number | null {
  if (value == null) return null
  const n = parseFloat(value)
  return isNaN(n) ? null : n
}

export function num(value: string | null | undefined): number {
  return parseDecimal(value) ?? 0
}

export function pnlToneClass(n: number): string {
  return n > 0 ? "text-profit" : n < 0 ? "text-loss" : "text-fg-1"
}

export function toneClass(tone: "profit" | "loss" | "neutral"): string {
  return tone === "profit" ? "text-profit" : tone === "loss" ? "text-loss" : "text-fg-1"
}
