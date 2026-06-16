import { useId } from "react"
import { Area, AreaChart, CartesianGrid, Tooltip, type TooltipProps, XAxis, YAxis } from "recharts"

import { useChartColors, useReducedMotion } from "./chart-theme"
import { ChartFrame } from "./ChartFrame"
import { ChartTooltip } from "./ChartTooltip"
import { buildTooltip } from "./tooltip"

interface AreaChartTLProps<T> {
  data: T[]
  xKey: keyof T & string
  yKey: keyof T & string
  height?: number
  xTickFormat?: (value: number) => string
  yTickFormat?: (value: number) => string
  tooltipLabel?: (value: number) => string
  tooltipValue: (value: number) => string
  tooltipDirectional?: boolean
  emptyHint?: string
}

export function AreaChartTL<T>({
  data, xKey, yKey, height = 240, xTickFormat, yTickFormat, tooltipLabel, tooltipValue, tooltipDirectional, emptyHint
}: AreaChartTLProps<T>) {
  const c = useChartColors()
  const noAnim = useReducedMotion()
  const uid = useId()
  const strokeId = `tl-area-stroke-${uid}`
  const fillId = `tl-area-fill-${uid}`

  const values = data.map(d => Number(d[yKey])).filter(Number.isFinite)
  const hi = values.length ? Math.max(0, ...values) : 1
  const lo = values.length ? Math.min(0, ...values) : 0
  const pad = (hi - lo) * 0.08 || 1
  const domainMax = hi + pad
  const domainMin = lo - pad
  // vertical position of the $0 line from the top of the plot (0..1)
  const zero = (domainMax - 0) / (domainMax - domainMin)
  const below = (frac: number) => Math.min(1, zero + (1 - zero) * frac)

  // green only ABOVE $0 (fades to lime by the zero line); below $0 -> lime -> yellow -> red
  const strokeStops = [
    { o: 0, color: c.profit },
    { o: zero, color: c.accent },
    { o: below(0.5), color: c.warn },
    { o: 1, color: c.loss }
  ]
  const fillStops = [
    { o: 0, color: c.profit, op: 0.26 },
    { o: zero, color: c.accent, op: 0.13 },
    { o: below(0.5), color: c.warn, op: 0.09 },
    { o: 1, color: c.loss, op: 0.05 }
  ]

  return (
    <ChartFrame height={height} empty={data.length < 2} emptyHint={emptyHint}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={strokeId} x1="0" y1="0" x2="0" y2="1">
            {strokeStops.map((s, i) => <stop key={i} offset={`${s.o * 100}%`} stopColor={s.color} />)}
          </linearGradient>
          <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
            {fillStops.map((s, i) => <stop key={i} offset={`${s.o * 100}%`} stopColor={s.color} stopOpacity={s.op} />)}
          </linearGradient>
        </defs>
        <CartesianGrid stroke={c.grid} strokeOpacity={0.5} vertical={false} />
        <XAxis
          dataKey={xKey}
          type="number"
          scale="time"
          domain={["dataMin", "dataMax"]}
          tickFormatter={xTickFormat}
          tick={{ fill: c.axis, fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: c.grid }}
          minTickGap={48}
        />
        <YAxis
          tickFormatter={yTickFormat}
          tick={{ fill: c.axis, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={52}
          domain={[domainMin, domainMax]}
        />
        <Tooltip
          cursor={{ stroke: c.grid }}
          content={(p: TooltipProps<number, string>) => {
            const t = buildTooltip<number>(p, tooltipLabel, tooltipValue, c.accent, tooltipDirectional ? { profit: c.profit, loss: c.loss } : undefined)
            return t ? <ChartTooltip {...t} /> : null
          }}
        />
        <Area
          type="monotone"
          dataKey={yKey}
          stroke={`url(#${strokeId})`}
          strokeWidth={2}
          fill={`url(#${fillId})`}
          isAnimationActive={!noAnim}
        />
      </AreaChart>
    </ChartFrame>
  )
}
