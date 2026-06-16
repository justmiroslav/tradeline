import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"
import { formatSignedUsd, toneClass } from "@/shared/lib/format"
import type { EquityPoint } from "@/shared/types/api"
import { Panel } from "@/shared/ui/Panel"

import { EquityCurve } from "../charts/EquityCurve"

export interface HeroStat {
  label: string
  value: string
  tone?: "neutral" | "profit" | "loss"
}

interface EquityHeroProps {
  netPnl: number
  stats: HeroStat[]
  equity: EquityPoint[]
  control?: ReactNode
  height?: number
  className?: string
}

export function EquityHero({ netPnl, stats, equity, control, height = 240, className }: EquityHeroProps) {
  const netTone = netPnl > 0 ? "text-profit" : netPnl < 0 ? "text-loss" : "text-fg-0"
  return (
    <Panel className={className}>
      <div className="flex flex-col lg:flex-row gap-4 sm:gap-5">
        <div className="lg:w-52 lg:shrink-0 flex flex-col gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-wide text-fg-2">Net P&L</div>
            <div className={cn("mono tnum text-[30px] sm:text-[34px] font-semibold leading-none mt-1.5", netTone)}>
              {formatSignedUsd(netPnl)}
            </div>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-1 gap-x-5 gap-y-1.5">
            {stats.map(s => (
              <div key={s.label} className="flex items-baseline justify-between gap-3 text-[12.5px]">
                <span className="text-fg-3 whitespace-nowrap">{s.label}</span>
                <span className={cn("mono tnum font-medium", toneClass(s.tone ?? "neutral"))}>
                  {s.value}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="flex-1 min-w-0 flex flex-col gap-2">
          {control && <div className="flex justify-end">{control}</div>}
          <EquityCurve points={equity} height={height} />
        </div>
      </div>
    </Panel>
  )
}
