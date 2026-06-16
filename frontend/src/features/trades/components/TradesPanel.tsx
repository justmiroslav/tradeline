import type { ReactNode } from "react"

import { JournalPanel, TRADES_PAGE_SIZE, TRADES_SPLIT, useJournalControls } from "@/features/journal"
import type { ListFilters, TradeOut } from "@/shared/types/api"

import { exportTradesCsv } from "../api"
import { TRADE_COLUMNS } from "../columns"
import { useTrades } from "../hooks"

interface TradesPanelProps {
  listFilters: ListFilters
  active: boolean
  filtersBar: ReactNode
  viewSwitch?: ReactNode
}

export function TradesPanel({ listFilters, active, filtersBar, viewSwitch }: TradesPanelProps) {
  const controls = useJournalControls(listFilters, () => exportTradesCsv(listFilters))
  const query = useTrades({ ...listFilters, page: controls.page, size: TRADES_PAGE_SIZE })

  return (
    <JournalPanel<TradeOut>
      query={query}
      columns={TRADE_COLUMNS}
      rowKey={t => t.id}
      controls={controls}
      active={active}
      noun="trade"
      nounPlural="trades"
      emptyHint="Connect an exchange API key to start seeing your trades here"
      filtersBar={filtersBar}
      viewSwitch={viewSwitch}
      split={TRADES_SPLIT}
    />
  )
}
