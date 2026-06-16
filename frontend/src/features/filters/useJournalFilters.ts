import { useState } from "react"
import { useLocation } from "react-router-dom"

import { type JournalView } from "./model"
import { useScopedFilters } from "./useScopedFilters"

export function useJournalFilters() {
  const location = useLocation()
  const trades = useScopedFilters("trades")
  const positions = useScopedFilters("positions")
  const [view, setView] = useState<JournalView>(
    () => (location.state as { view?: JournalView } | null)?.view === "positions" ? "positions" : "trades"
  )

  const active = view === "trades" ? trades : positions

  return {
    view,
    setView,
    filters: active.filters,
    setFilters: active.setFilters,
    reset: active.reset,
    tradeFilters: trades.filters,
    positionFilters: positions.filters
  }
}
