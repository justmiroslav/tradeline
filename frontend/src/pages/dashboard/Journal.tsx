import { useQueryClient } from "@tanstack/react-query"
import { useEffect, useMemo } from "react"

import { TopBar } from "@/app/shell/TopBar"
import { useApiKeys } from "@/features/api-keys"
import {
  collapseAllTickers,
  FiltersBar,
  isFilterActive,
  type JournalView,
  toPositionFilters,
  toTradeFilters,
  useJournalFilters,
  usePeriodOptions
} from "@/features/filters"
import { JOURNAL_PAGE_SIZE, TRADES_PAGE_SIZE } from "@/features/journal"
import { listPositionsRequest, PositionsPanel, positionsQueryKey } from "@/features/positions"
import { listTradesRequest, TradesPanel, tradesQueryKey, useTradeSymbols } from "@/features/trades"
import { withViewTransition } from "@/shared/lib/viewTransition"
import { Segmented } from "@/shared/ui/Segmented"

const VIEW_OPTIONS = [
  { value: "trades" as const, label: "Trades" },
  { value: "positions" as const, label: "Positions" }
]

export default function Journal() {
  const queryClient = useQueryClient()
  const { filters, view, setFilters, setView, reset, tradeFilters: tradeState, positionFilters: positionState } = useJournalFilters()
  const symbolOptions = useTradeSymbols().data ?? []
  const keys = useApiKeys().data ?? []
  const { periodOptions, periodMin, periodMax } = usePeriodOptions()

  const tradeFilters = useMemo(
    () => toTradeFilters(collapseAllTickers(tradeState, symbolOptions.length), tradeState.keys),
    [tradeState, symbolOptions.length]
  )
  const positionFilters = useMemo(
    () => toPositionFilters(collapseAllTickers(positionState, symbolOptions.length), positionState.keys),
    [positionState, symbolOptions.length]
  )
  const active = isFilterActive(filters, view)

  useEffect(() => {
    if (view === "trades") {
      const params = { ...positionFilters, page: 1, size: JOURNAL_PAGE_SIZE }
      void queryClient.prefetchQuery({ queryKey: positionsQueryKey(params), queryFn: () => listPositionsRequest(params), staleTime: 10_000 })
    } else {
      const params = { ...tradeFilters, page: 1, size: TRADES_PAGE_SIZE }
      void queryClient.prefetchQuery({ queryKey: tradesQueryKey(params), queryFn: () => listTradesRequest(params), staleTime: 10_000 })
    }
  }, [view, tradeFilters, positionFilters, queryClient])

  const filtersBar = (
    <FiltersBar
      filters={filters}
      onChange={setFilters}
      active={active}
      keys={keys}
      symbolOptions={symbolOptions}
      periodOptions={periodOptions}
      periodMin={periodMin}
      periodMax={periodMax}
      showSide={view === "positions"}
      showStatus={view === "positions"}
      onReset={reset}
    />
  )

  const viewSwitch = (
    <Segmented<JournalView>
      ariaLabel="Journal view"
      value={view}
      onChange={v => withViewTransition(() => setView(v))}
      options={VIEW_OPTIONS}
      variant="flat"
      size="sm"
    />
  )

  return (
    <>
      <TopBar title="Journal" />
      <div className="flex-1 min-h-0 flex flex-col gap-4 p-4 sm:p-7 overflow-hidden">
        {view === "trades"
          ? <TradesPanel listFilters={tradeFilters} active={active} filtersBar={filtersBar} viewSwitch={viewSwitch} />
          : <PositionsPanel listFilters={positionFilters} active={active} filtersBar={filtersBar} viewSwitch={viewSwitch} />}
      </div>
    </>
  )
}
