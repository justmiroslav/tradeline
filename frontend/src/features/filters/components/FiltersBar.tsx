import { useMemo } from "react"

import { EXCHANGE_CAPS } from "@/shared/lib/exchange-caps"
import { withViewTransition } from "@/shared/lib/viewTransition"
import type { ApiKeyOut, Exchange, MarketType } from "@/shared/types/api"
import { Btn } from "@/shared/ui/Btn"
import { ExchangeMark } from "@/shared/ui/ExchangeMark"
import { Ico } from "@/shared/ui/Ico"
import { Segmented } from "@/shared/ui/Segmented"

import { type JournalFilterState, type PeriodPreset } from "../model"
import { FilterDropdown, type FilterOption } from "./FilterDropdown"
import { type MultiOption, MultiSelectFilter } from "./MultiSelectFilter"
import { PeriodFilter } from "./PeriodFilter"

interface FiltersBarProps {
  filters: JournalFilterState
  onChange: (next: JournalFilterState) => void
  active: boolean
  keys: ApiKeyOut[]
  symbolOptions: string[]
  periodOptions: { value: PeriodPreset; label: string }[]
  periodMin: string | null
  periodMax: string | null
  showSide?: boolean
  showStatus?: boolean
  showPeriod?: boolean
  onReset: () => void
}

const SIDE_FILTER_OPTIONS: FilterOption<"all" | "long" | "short">[] = [
  { value: "all", label: "Long & short" },
  { value: "long", label: "Long only" },
  { value: "short", label: "Short only" }
]

const STATUS_FILTER_OPTIONS: FilterOption<"all" | "open" | "closed">[] = [
  { value: "all", label: "Open & closed" },
  { value: "open", label: "Open only" },
  { value: "closed", label: "Closed only" }
]

export function FiltersBar({ filters, onChange, active, keys, symbolOptions, periodOptions, periodMin, periodMax, showSide, showStatus, showPeriod = true, onReset }: FiltersBarProps) {
  const change = (next: JournalFilterState) => withViewTransition(() => onChange(next))
  const set = <K extends keyof JournalFilterState>(key: K, value: JournalFilterState[K]) =>
    change({ ...filters, [key]: value })

  const exchangeOptions = useMemo(() => exchangeOptionsFrom(keys), [keys])
  const keyOptions = useMemo(() => keyOptionsFrom(keys), [keys])
  const tickerOptions: MultiOption<string>[] = symbolOptions.map(s => ({ value: s, label: s }))

  return (
    <div className="flex flex-wrap items-center gap-1">
      <MultiSelectFilter
        ariaLabel="Filter by exchange"
        allLabel="All exchanges"
        emptyLabel="No exchanges"
        noun="exchanges"
        selected={filters.exchanges}
        options={exchangeOptions}
        onChange={(v) => set("exchanges", v)}
      />

      <MultiSelectFilter
        ariaLabel="Filter by API key"
        allLabel="All keys"
        emptyLabel="No keys"
        noun="keys"
        selected={filters.keys}
        options={keyOptions}
        onChange={(v) => set("keys", v)}
      />

      <Segmented<"all" | MarketType>
        size="sm"
        ariaLabel="Filter by market"
        value={filters.market ?? "all"}
        onChange={(v) => set("market", v === "all" ? null : v)}
        options={[{ value: "all", label: "All" }, { value: "spot", label: "Spot" }, { value: "futures", label: "Futures" }]}
      />

      <MultiSelectFilter
        ariaLabel="Filter by ticker"
        allLabel="All tickers"
        emptyLabel="No tickers yet"
        noun="tickers"
        searchable
        searchPlaceholder="Search tickers"
        selected={filters.tickers}
        options={tickerOptions}
        onChange={(v) => set("tickers", v)}
      />

      {showSide && (
        <FilterDropdown
          ariaLabel="Filter by direction"
          value={filters.side ?? "all"}
          options={SIDE_FILTER_OPTIONS}
          onChange={(v) => set("side", v === "all" ? null : v)}
        />
      )}
      {showStatus && (
        <FilterDropdown
          ariaLabel="Filter by status"
          value={filters.status ?? "all"}
          options={STATUS_FILTER_OPTIONS}
          onChange={(v) => set("status", v === "all" ? null : v)}
        />
      )}

      {showPeriod && (
        <PeriodFilter
          period={filters.period}
          customFrom={filters.customFrom}
          customTo={filters.customTo}
          presets={periodOptions}
          min={periodMin}
          max={periodMax}
          onPreset={(p) => change({ ...filters, period: p, customFrom: null, customTo: null })}
          onCustom={(from, to) => change({ ...filters, period: "custom", customFrom: from, customTo: to })}
        />
      )}

      {active && (
        <Btn kind="ghost" size="sm" onClick={() => withViewTransition(onReset)} leading={<Ico.X width={13} height={13} />}>
          Clear
        </Btn>
      )}
    </div>
  )
}

function exchangeOptionsFrom(keys: ApiKeyOut[]): MultiOption<Exchange>[] {
  const seen = new Set<Exchange>()
  const out: MultiOption<Exchange>[] = []
  for (const k of keys) {
    if (seen.has(k.exchange)) continue
    seen.add(k.exchange)
    out.push({ value: k.exchange, label: EXCHANGE_CAPS[k.exchange].name, icon: <ExchangeMark name={k.exchange} size={16} /> })
  }
  return out
}

function keyOptionsFrom(keys: ApiKeyOut[]): MultiOption<string>[] {
  return keys.map(k => ({
    value: k.id,
    label: k.label || EXCHANGE_CAPS[k.exchange].name,
    icon: <ExchangeMark name={k.exchange} size={16} />
  }))
}
