import { PnlCell, SidePill, StatusPill, SymbolCell } from "@/features/journal"
import { formatAmount, formatDateTimeShort, formatPercent, humanizeLabel } from "@/shared/lib/format"
import type { PositionOut } from "@/shared/types/api"
import type { Column } from "@/shared/ui/DataTable"

export const POSITION_COLUMNS: Column<PositionOut>[] = [
  { key: "opened", header: "Opened", width: "108px", hint: "When the position was entered", cell: p => <span className="mono tnum text-fg-2 truncate">{formatDateTimeShort(p.opened_at)}</span> },
  { key: "closed", header: "Closed", width: "108px", hint: "When the position was fully exited — realized P&L is dated here, which is how analytics and the calendar count it", cell: p => p.closed_at ? <span className="mono tnum text-fg-2 truncate">{formatDateTimeShort(p.closed_at)}</span> : <span className="text-fg-3">—</span> },
  { key: "symbol", header: "Symbol", width: "108px", cell: p => <SymbolCell exchange={p.exchange} symbol={p.symbol} /> },
  { key: "market", header: "Market", width: "66px", cell: p => <span className="text-fg-1 capitalize truncate">{p.market_type}</span> },
  { key: "side", header: "Side", width: "54px", align: "center", cell: p => <SidePill side={p.side} /> },
  { key: "status", header: "Status", width: "92px", align: "center", cell: p => <StatusPill status={p.status} /> },
  { key: "size", header: "Size", width: "80px", hint: "Position size in the base asset", cell: p => <span className="mono tnum text-fg-0 truncate">{formatAmount(p.size)}</span> },
  { key: "entry", header: "Entry", width: "80px", cell: p => <span className="mono tnum text-fg-0 truncate">{formatAmount(p.entry_price)}</span> },
  { key: "exit", header: "Exit", width: "80px", cell: p => <span className="mono tnum text-fg-1 truncate">{formatAmount(p.exit_price)}</span> },
  { key: "fees", header: "Fees", width: "74px", cell: p => <span className="mono tnum text-fg-2 truncate">{formatAmount(p.fees_quote)}</span> },
  { key: "pnl", header: "Net P&L", width: "92px", hint: "Realized profit after fees for the full round-trip", cell: p => p.status === "incomplete" ? <span className="text-fg-3">—</span> : <PnlCell value={p.net_pnl} /> },
  { key: "setup", header: "Setup", width: "112px", hint: "Detected trade setup from market context at entry", cell: p => p.setup ? <span className="text-fg-1 truncate inline-block max-w-full">{humanizeLabel(p.setup)}</span> : <span className="text-fg-3">—</span> },
  { key: "mfe", header: "MFE", width: "74px", hint: "Maximum favorable excursion — the best unrealized move in your favor (vs entry price) while the position was open, from 15m candles", cell: p => <span className="mono tnum text-profit/80 truncate">{formatPercent(p.mfe)}</span> },
  { key: "mae", header: "MAE", width: "74px", hint: "Maximum adverse excursion — the worst unrealized move against you (vs entry price) while the position was open, from 15m candles", cell: p => <span className="mono tnum text-loss/80 truncate">{formatPercent(p.mae)}</span> }
]
