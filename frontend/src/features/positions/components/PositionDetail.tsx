import { Fragment, type PointerEvent as ReactPointerEvent } from "react"

import { PnlCell, SidePill, StatusPill } from "@/features/journal"
import { useTrades } from "@/features/trades"
import { cn } from "@/shared/lib/cn"
import { formatAmount, formatDateTimeShort } from "@/shared/lib/format"
import type { PositionOut } from "@/shared/types/api"
import { ExchangeMark } from "@/shared/ui/ExchangeMark"

export interface DragHandle {
  onPointerDown: (e: ReactPointerEvent) => void
  className: string
}

const COLS = "grid-cols-[42px_100px_54px_72px]"

export function PositionDetail({ position: p, dragHandle }: { position: PositionOut; dragHandle: DragHandle }) {
  const { data, isPending } = useTrades({
    api_key_ids: [p.api_key_id],
    symbols: [p.symbol],
    date_from: p.opened_at,
    date_to: p.closed_at ?? undefined,
    size: 100
  })
  const trades = data?.items ?? []

  return (
    <div className="w-[360px] max-w-[calc(100vw-24px)]">
      <div onPointerDown={dragHandle.onPointerDown} className={cn("flex flex-col gap-1.5 px-3.5 pt-3 pb-2.5 border-b border-line", dragHandle.className)}>
        <div className="flex items-center gap-2 pr-7">
          <ExchangeMark name={p.exchange} size={16} />
          <span className="text-[13.5px] font-semibold text-fg-0 truncate">{p.symbol}</span>
          <SidePill side={p.side} />
          <StatusPill status={p.status} />
          {p.status !== "incomplete" && <span className="ml-auto text-[13px]"><PnlCell value={p.net_pnl} /></span>}
        </div>
        <span className="text-[11px] text-fg-2 mono tnum">
          {formatDateTimeShort(p.opened_at)} → {p.closed_at ? formatDateTimeShort(p.closed_at) : "open"}
        </span>
      </div>

      <div className="px-3.5 py-3">
        {isPending ? (
          <div className="text-[12px] text-fg-2">Loading…</div>
        ) : trades.length === 0 ? (
          <div className="text-[12px] text-fg-3">No trades in this window</div>
        ) : (
          <>
            <div className={cn("grid items-center gap-x-3 mb-2 text-[10px] uppercase tracking-[0.07em] text-fg-3", COLS)}>
              <span />
              <span>Time</span>
              <span className="text-right">Qty</span>
              <span className="text-right">Price</span>
            </div>
            <div className="max-h-[80px] overflow-y-auto tl-scroll-thin pr-1">
              <div className={cn("grid items-center gap-x-3 gap-y-2.5 text-[12px]", COLS)}>
                {trades.map(t => (
                  <Fragment key={t.id}>
                    <span className="flex justify-center"><SidePill side={t.side} /></span>
                    <span className="mono tnum text-fg-2 whitespace-nowrap">{formatDateTimeShort(t.time)}</span>
                    <span className="mono tnum text-fg-0 text-right">{formatAmount(t.quantity)}</span>
                    <span className="mono tnum text-fg-0 text-right">{formatAmount(t.price)}</span>
                  </Fragment>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
