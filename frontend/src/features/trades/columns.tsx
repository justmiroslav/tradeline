import { SidePill, SymbolCell } from "@/features/journal"
import { formatAmount, formatDateTimeShort } from "@/shared/lib/format"
import type { TradeOut } from "@/shared/types/api"
import type { Column } from "@/shared/ui/DataTable"

export const TRADE_COLUMNS: Column<TradeOut>[] = [
  { key: "time", header: "Time", width: "118px", cell: t => <span className="mono tnum text-fg-2 truncate">{formatDateTimeShort(t.time)}</span> },
  { key: "symbol", header: "Symbol", width: "108px", cell: t => <SymbolCell exchange={t.exchange} symbol={t.symbol} /> },
  { key: "market", header: "Market", width: "66px", cell: t => <span className="text-fg-1 capitalize truncate">{t.market_type}</span> },
  { key: "side", header: "Side", width: "54px", align: "center", cell: t => <SidePill side={t.side} /> },
  { key: "qty", header: "Qty", width: "82px", cell: t => <span className="mono tnum text-fg-0 truncate">{formatAmount(t.quantity)}</span> },
  { key: "price", header: "Price", width: "82px", cell: t => <span className="mono tnum text-fg-0 truncate">{formatAmount(t.price)}</span> },
  { key: "fee", header: "Fee", width: "76px", cell: t => <span className="mono tnum text-fg-2 truncate">{formatAmount(t.fee)}</span> }
]
