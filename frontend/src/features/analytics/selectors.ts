import { num } from "@/shared/lib/format"
import type { BucketStat, DailyPnl, EquityPoint } from "@/shared/types/api"

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

export interface EquitySample {
  t: number
  equity: number
}

export interface DailyBar {
  date: string
  net: number
  count: number
}

export interface BucketBar {
  key: string
  net: number
  count: number
  winRate: number
  avgPnl: number
  volume: number
}

function toBar(b: BucketStat): BucketBar {
  return { key: b.key, net: num(b.net_pnl), count: b.count, winRate: b.win_rate, avgPnl: num(b.avg_pnl), volume: num(b.volume) }
}

function emptyBar(key: string): BucketBar {
  return { key, net: 0, count: 0, winRate: 0, avgPnl: 0, volume: 0 }
}

const HOUR_MS = 3_600_000
const DAY_MS = 24 * HOUR_MS
const STEP_LADDER = [HOUR_MS, 2 * HOUR_MS, 3 * HOUR_MS, 6 * HOUR_MS, 12 * HOUR_MS, DAY_MS, 2 * DAY_MS, 3 * DAY_MS, 7 * DAY_MS]
const TARGET_SAMPLES = 80

function pickStep(spanMs: number): number {
  const target = spanMs / TARGET_SAMPLES
  return STEP_LADDER.find(s => s >= target) ?? STEP_LADDER[STEP_LADDER.length - 1]
}

export function toEquitySeries(points: EquityPoint[]): EquitySample[] {
  if (points.length === 0) return []
  const raw = points
    .map(p => ({ t: new Date(p.time).getTime(), equity: num(p.equity) }))
    .sort((a, b) => a.t - b.t)

  const first = raw[0].t
  const last = raw[raw.length - 1].t
  const span = last - first
  if (span <= 0) return [{ t: first - HOUR_MS, equity: 0 }, ...raw]

  const step = pickStep(span)
  const out: EquitySample[] = [{ t: first - step, equity: 0 }]
  let idx = 0
  let val = 0
  for (let ts = first; ts < last; ts += step) {
    while (idx < raw.length && raw[idx].t <= ts) val = raw[idx++].equity
    out.push({ t: ts, equity: val })
  }
  while (idx < raw.length) val = raw[idx++].equity
  out.push({ t: last, equity: val })
  return out
}

export function toDailyBars(daily: DailyPnl[]): DailyBar[] {
  return daily.map(d => ({ date: d.date, net: num(d.net_pnl), count: d.count }))
}

export function toBucketBars(buckets: BucketStat[], limit?: number): BucketBar[] {
  const bars = buckets.map(toBar)
  bars.sort((a, b) => Math.abs(b.net) - Math.abs(a.net))
  return limit ? bars.slice(0, limit) : bars
}

export function toHourBars(buckets: BucketStat[]): BucketBar[] {
  const map = new Map(buckets.map(b => [b.key, toBar(b)]))
  return Array.from({ length: 24 }, (_, h) => map.get(String(h)) ?? emptyBar(String(h)))
}

export function toWeekdayBars(buckets: BucketStat[]): BucketBar[] {
  const map = new Map(buckets.map(b => [b.key, toBar(b)]))
  return WEEKDAY_LABELS.map((label, i) => {
    const b = map.get(String(i))
    return b ? { ...b, key: label } : emptyBar(label)
  })
}

export function toSideBars(buckets: BucketStat[]): BucketBar[] {
  const map = new Map(buckets.map(b => [b.key.toUpperCase(), toBar(b)]))
  return ["LONG", "SHORT"].flatMap(side => {
    const bar = map.get(side)
    return bar ? [{ ...bar, key: side === "LONG" ? "Long" : "Short" }] : []
  })
}

export function toMarketBars(buckets: BucketStat[]): BucketBar[] {
  const map = new Map(buckets.map(b => [b.key.toLowerCase(), toBar(b)]))
  return ["spot", "futures"].flatMap(market => {
    const bar = map.get(market)
    return bar ? [{ ...bar, key: market === "spot" ? "Spot" : "Futures" }] : []
  })
}
