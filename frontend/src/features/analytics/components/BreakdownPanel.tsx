import { useState } from "react"

import { humanizeLabel } from "@/shared/lib/format"
import type { AnalyticsOut } from "@/shared/types/api"
import { CarouselArrow } from "@/shared/ui/CarouselArrow"
import { Panel } from "@/shared/ui/Panel"

import { BucketBarChart } from "../charts/BucketBarChart"
import { toBucketBars, toHourBars, toMarketBars, toSideBars, toWeekdayBars } from "../selectors"

type Dim = "symbol" | "setup" | "side" | "day" | "hour" | "market"

const DIMS: { value: Dim; label: string }[] = [
  { value: "symbol", label: "Symbol" },
  { value: "setup", label: "Setup" },
  { value: "side", label: "Side" },
  { value: "day", label: "Day" },
  { value: "hour", label: "Hour" },
  { value: "market", label: "Market" }
]

interface BreakdownPanelProps {
  a: AnalyticsOut
  className?: string
  onToggleTicker: (key: string) => void
  onToggleSide: (key: string) => void
  onToggleMarket: (key: string) => void
}

export function BreakdownPanel({ a, className, onToggleTicker, onToggleSide, onToggleMarket }: BreakdownPanelProps) {
  const [idx, setIdx] = useState(0)
  const dim = DIMS[idx].value
  const go = (d: number) => setIdx((idx + d + DIMS.length) % DIMS.length)

  return (
    <Panel
      title="Performance by"
      className={className}
      action={
        <div className="flex items-center gap-0.5">
          <CarouselArrow dir="prev" label="Previous dimension" onClick={() => go(-1)} />
          <span className="text-[11px] font-medium text-fg-1 w-[58px] text-center">{DIMS[idx].label}</span>
          <CarouselArrow dir="next" label="Next dimension" onClick={() => go(1)} />
        </div>
      }
    >
      <div key={dim} className="animate-tl-fade-soft">
        {dim === "symbol" && <BucketBarChart bars={toBucketBars(a.by_symbol)} onSelect={onToggleTicker} height={170} scrollAfter={11} minBarWidth={46} />}
        {dim === "setup" && <BucketBarChart bars={toBucketBars(a.by_setup)} xFormat={humanizeLabel} height={170} />}
        {dim === "side" && <BucketBarChart bars={toSideBars(a.by_side)} onSelect={onToggleSide} height={170} />}
        {dim === "day" && <BucketBarChart bars={toWeekdayBars(a.by_weekday)} height={170} />}
        {dim === "hour" && <BucketBarChart bars={toHourBars(a.by_hour)} xFormat={h => `${h}h`} height={170} />}
        {dim === "market" && <BucketBarChart bars={toMarketBars(a.by_market)} onSelect={onToggleMarket} height={170} />}
      </div>
    </Panel>
  )
}
