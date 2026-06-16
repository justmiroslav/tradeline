import { formatCompactUsd, formatSignedUsd } from "@/shared/lib/format"
import { BarChartTL } from "@/shared/ui/charts"

import type { BucketBar } from "../selectors"

interface BucketBarChartProps {
  bars: BucketBar[]
  height?: number
  xFormat?: (key: string) => string
  onSelect?: (key: string) => void
  scrollAfter?: number
  minBarWidth?: number
}

export function BucketBarChart({ bars, height = 200, xFormat, onSelect, scrollAfter, minBarWidth }: BucketBarChartProps) {
  const label = xFormat ?? ((k: string) => k)
  return (
    <BarChartTL
      data={bars}
      xKey="key"
      yKey="net"
      height={height}
      xTickFormat={label}
      yTickFormat={formatCompactUsd}
      tooltipLabel={label}
      tooltipValue={formatSignedUsd}
      emptyHint="No data in this range"
      onBarClick={onSelect ? b => onSelect(b.key) : undefined}
      scrollAfter={scrollAfter}
      minBarWidth={minBarWidth}
      maxBarSize={28}
    />
  )
}
