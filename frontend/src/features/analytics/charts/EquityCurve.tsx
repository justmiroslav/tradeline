import { formatCompactUsd, formatDateCompact, formatDateTime, formatSignedUsd } from "@/shared/lib/format"
import type { EquityPoint } from "@/shared/types/api"
import { AreaChartTL } from "@/shared/ui/charts"

import { toEquitySeries } from "../selectors"

interface EquityCurveProps {
  points: EquityPoint[]
  height?: number
}

export function EquityCurve({ points, height }: EquityCurveProps) {
  const data = toEquitySeries(points)
  return (
    <AreaChartTL
      data={data}
      xKey="t"
      yKey="equity"
      height={height}
      xTickFormat={t => formatDateCompact(new Date(t))}
      yTickFormat={formatCompactUsd}
      tooltipLabel={t => formatDateTime(new Date(t).toISOString())}
      tooltipValue={formatSignedUsd}
      tooltipDirectional
      emptyHint="Equity curve appears after a few closed positions"
    />
  )
}
