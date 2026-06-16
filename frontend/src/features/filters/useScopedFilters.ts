import { createContext, useCallback, useContext, useMemo } from "react"

import { EMPTY_JOURNAL_FILTERS, type JournalFilterState } from "./model"

export type FilterScope = "trades" | "positions" | "analytics"

export interface ScopedFiltersValue {
  filters: JournalFilterState
  setFilters: (filters: JournalFilterState) => void
  reset: () => void
}

export interface FiltersStore {
  state: Record<FilterScope, JournalFilterState>
  set: (scope: FilterScope, filters: JournalFilterState) => void
}

export const FiltersContext = createContext<FiltersStore | null>(null)

export function useScopedFilters(scope: FilterScope): ScopedFiltersValue {
  const store = useContext(FiltersContext)
  if (!store) throw new Error("useScopedFilters must be used within FiltersProvider")
  const { state, set } = store
  const filters = state[scope]
  const setFilters = useCallback((next: JournalFilterState) => set(scope, next), [set, scope])
  const reset = useCallback(() => set(scope, EMPTY_JOURNAL_FILTERS), [set, scope])
  return useMemo(() => ({ filters, setFilters, reset }), [filters, setFilters, reset])
}
