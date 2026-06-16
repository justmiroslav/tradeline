import type { Exchange, ListFilters, MarketType, PositionSide, PositionStatus } from "@/shared/types/api"

export type JournalView = "trades" | "positions"
export type PeriodPreset = "all" | "7d" | "30d" | "90d" | "1y" | "custom"

export interface JournalFilterState {
  exchanges: Exchange[]
  keys: string[]
  market: MarketType | null
  tickers: string[]
  period: PeriodPreset
  customFrom: string | null
  customTo: string | null
  side: PositionSide | null
  status: PositionStatus | null
}

export interface PositionListFilters extends ListFilters {
  status?: PositionStatus
}

export const EMPTY_JOURNAL_FILTERS: JournalFilterState = {
  exchanges: [], keys: [], market: null, tickers: [], period: "all", customFrom: null, customTo: null, side: null, status: null
}

const PRESET_DAYS: { value: PeriodPreset; label: string; days: number }[] = [
  { value: "7d", label: "Last 7 days", days: 7 },
  { value: "30d", label: "Last 30 days", days: 30 },
  { value: "90d", label: "Last 90 days", days: 90 },
  { value: "1y", label: "Last year", days: 365 }
]

export function periodPresets(spanDays: number | null | undefined): { value: PeriodPreset; label: string }[] {
  const span = spanDays ?? 0
  const out: { value: PeriodPreset; label: string }[] = [{ value: "all", label: "All time" }]
  for (const p of PRESET_DAYS) if (span > p.days) out.push({ value: p.value, label: p.label })
  return out
}

function periodFrom(period: PeriodPreset): string | undefined {
  const now = new Date()
  const start = new Date(now)
  switch (period) {
    case "7d": start.setDate(now.getDate() - 7); break
    case "30d": start.setDate(now.getDate() - 30); break
    case "90d": start.setDate(now.getDate() - 90); break
    case "1y": start.setFullYear(now.getFullYear() - 1); break
    default: return undefined
  }
  return start.toISOString()
}

export function toTradeFilters(f: JournalFilterState, apiKeyIds: string[]): ListFilters {
  const params: ListFilters = {}
  if (f.exchanges.length) params.exchanges = f.exchanges
  if (apiKeyIds.length) params.api_key_ids = apiKeyIds
  if (f.market) params.market_types = [f.market]
  if (f.tickers.length) params.symbols = f.tickers
  if (f.period === "custom") {
    if (f.customFrom) params.date_from = f.customFrom
    if (f.customTo) params.date_to = f.customTo
  } else {
    const from = periodFrom(f.period)
    if (from) params.date_from = from
  }
  return params
}

export function toPositionFilters(f: JournalFilterState, apiKeyIds: string[]): PositionListFilters {
  const params: PositionListFilters = toTradeFilters(f, apiKeyIds)
  if (f.side) params.sides = [f.side]
  if (f.status) params.status = f.status
  return params
}

export function toAnalyticsFilters(f: JournalFilterState, apiKeyIds: string[]): ListFilters {
  const params = toTradeFilters(f, apiKeyIds)
  if (f.side) params.sides = [f.side]
  return params
}

export function periodToAnalyticsFilters(period: PeriodPreset): ListFilters {
  const from = periodFrom(period)
  return from ? { date_from: from } : {}
}

export function collapseAllTickers(f: JournalFilterState, symbolCount: number): JournalFilterState {
  const allSelected = symbolCount > 0 && f.tickers.length >= symbolCount
  return allSelected ? { ...f, tickers: [] } : f
}

export function isFilterActive(f: JournalFilterState, view: JournalView | "analytics"): boolean {
  const shared = f.exchanges.length > 0 || f.keys.length > 0
    || f.market != null || f.tickers.length > 0 || f.period !== "all"
  if (view === "trades") return shared
  if (view === "analytics") return shared || f.side != null
  return shared || f.side != null || f.status != null
}
