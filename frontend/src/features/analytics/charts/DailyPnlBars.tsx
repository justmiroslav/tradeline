import { formatCompactUsd, formatDayFull, formatDayLabel, formatSignedUsd } from "@/shared/lib/format"
import type { DailyPnl } from "@/shared/types/api"
import { BarChartTL } from "@/shared/ui/charts"

import { toDailyBars } from "../selectors"

interface DailyPnlBarsProps {
  daily: DailyPnl[]
  height?: number
  scrollAfter?: number
  minBarWidth?: number
}

export function DailyPnlBars({ daily, height, scrollAfter, minBarWidth }: DailyPnlBarsProps) {
  const data = toDailyBars(daily)
  return (
    <BarChartTL
      data={data}
      xKey="date"
      yKey="net"
      height={height}
      xTickFormat={formatDayLabel}
      yTickFormat={formatCompactUsd}
      tooltipLabel={formatDayFull}
      tooltipValue={formatSignedUsd}
      emptyHint="No closed positions in this range"
      scrollAfter={scrollAfter}
      minBarWidth={minBarWidth}
    />
  )
}
