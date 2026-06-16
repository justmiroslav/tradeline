import { cn } from "@/shared/lib/cn"
import { formatSignedUsd, pnlToneClass } from "@/shared/lib/format"
import type { Exchange, PositionStatus } from "@/shared/types/api"
import { ExchangeMark } from "@/shared/ui/ExchangeMark"
import { Pill } from "@/shared/ui/Pill"

const POSITIVE_SIDES = new Set(["buy", "long"])

export function SymbolCell({ exchange, symbol }: { exchange: Exchange; symbol: string }) {
  return (
    <span className="flex items-center gap-2 min-w-0">
      <ExchangeMark name={exchange} size={18} />
      <span className="text-fg-0 font-medium truncate">{symbol}</span>
    </span>
  )
}

export function SidePill({ side }: { side: string }) {
  return (
    <Pill tone={POSITIVE_SIDES.has(side) ? "profit" : "loss"} className="text-[10.5px] px-1.5 py-0 capitalize">
      {side}
    </Pill>
  )
}

export function StatusPill({ status }: { status: PositionStatus }) {
  if (status === "open") return <Pill tone="accent" dot="live" className="text-[10.5px] px-1.5 py-0">open</Pill>
  if (status === "incomplete") return <Pill tone="warn" className="text-[10.5px] px-1.5 py-0">incomplete</Pill>
  return <Pill tone="neutral" className="text-[10.5px] px-1.5 py-0">closed</Pill>
}

export function PnlCell({ value }: { value: number }) {
  return <span className={cn("mono tnum font-medium", pnlToneClass(value))}>{formatSignedUsd(value)}</span>
}
