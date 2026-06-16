import { type ReactNode, useCallback, useMemo, useState } from "react"

import { EMPTY_JOURNAL_FILTERS, type JournalFilterState } from "./model"
import { FiltersContext, type FilterScope } from "./useScopedFilters"

const INITIAL: Record<FilterScope, JournalFilterState> = {
  trades: EMPTY_JOURNAL_FILTERS,
  positions: EMPTY_JOURNAL_FILTERS,
  analytics: EMPTY_JOURNAL_FILTERS
}

export function FiltersProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState(INITIAL)
  const set = useCallback((scope: FilterScope, filters: JournalFilterState) => setState(prev => ({ ...prev, [scope]: filters })), [])
  const value = useMemo(() => ({ state, set }), [state, set])
  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>
}
