import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, Tooltip, type TooltipProps, XAxis, YAxis } from "recharts"

import { useReducedMotion } from "./chart-theme"
import { ChartFrame } from "./ChartFrame"
import { ChartTooltip } from "./ChartTooltip"
import { buildTooltip } from "./tooltip"

interface BarChartTLProps<T> {
  data: T[]
  xKey: keyof T & string
  yKey: keyof T & string
  height?: number
  xTickFormat?: (value: string) => string
  yTickFormat?: (value: number) => string
  tooltipLabel?: (value: string) => string
  tooltipValue: (value: number) => string
  emptyHint?: string
  onBarClick?: (datum: T) => void
  scrollAfter?: number
  minBarWidth?: number
  maxBarSize?: number
}

const Y_AXIS_W = 50
const X_AXIS_H = 22
const SCROLLBAR_LANE = 14

export function BarChartTL<T>({
  data, xKey, yKey, height = 200, xTickFormat, yTickFormat, tooltipLabel, tooltipValue, emptyHint, onBarClick, scrollAfter, minBarWidth = 48, maxBarSize = 40
}: BarChartTLProps<T>) {
  const noAnim = useReducedMotion()
  const scroll = data.length > 0 && scrollAfter != null && data.length > scrollAfter
  const scrollWidth = scroll ? data.length * minBarWidth : 0

  const tooltip = (
    <Tooltip
      cursor={{ opacity: 0.3 }}
      content={(p: TooltipProps<number, string>) => {
        const t = buildTooltip<string>(p, tooltipLabel, tooltipValue, "var(--accent)")
        return t ? <ChartTooltip {...t} /> : null
      }}
    />
  )

  const bars = (
    <Bar
      dataKey={yKey}
      radius={[3, 3, 0, 0]}
      maxBarSize={maxBarSize}
      isAnimationActive={!noAnim}
      cursor={onBarClick ? "pointer" : undefined}
      onClick={onBarClick ? (_: unknown, index: number) => { const d = data[index]; if (d) onBarClick(d) } : undefined}
    >
      {data.map((d, i) => (
        <Cell key={i} className={Number(d[yKey]) >= 0 ? "tl-bar-up" : "tl-bar-down"} />
      ))}
    </Bar>
  )

  if (scroll) {
    const plotHeight = height - SCROLLBAR_LANE
    return (
      <div className="relative w-full" style={{ height }}>
        <div className="absolute top-0 left-0 z-[1] bg-bg-1" style={{ width: Y_AXIS_W, height: plotHeight }}>
          <BarChart width={Y_AXIS_W} height={plotHeight} data={data} margin={{ top: 8, right: 0, bottom: 0, left: 0 }}>
            <XAxis dataKey={xKey} height={X_AXIS_H} tick={false} tickLine={false} />
            <YAxis tickFormatter={yTickFormat} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={Y_AXIS_W} />
            <Bar dataKey={yKey} fill="transparent" isAnimationActive={false} />
          </BarChart>
        </div>
        <div className="overflow-x-auto tl-scroll-thin" style={{ marginLeft: Y_AXIS_W, height }}>
          <BarChart width={scrollWidth} height={plotHeight} data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid strokeOpacity={0.5} vertical={false} />
            <XAxis dataKey={xKey} tickFormatter={xTickFormat} height={X_AXIS_H} tick={{ fontSize: 11 }} tickLine={false} minTickGap={24} />
            <YAxis hide />
            <ReferenceLine y={0} />
            {tooltip}
            {bars}
          </BarChart>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full" style={{ height }}>
      <ChartFrame height={height - SCROLLBAR_LANE} empty={data.length === 0} emptyHint={emptyHint}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeOpacity={0.5} vertical={false} />
          <XAxis dataKey={xKey} tickFormatter={xTickFormat} height={X_AXIS_H} tick={{ fontSize: 11 }} tickLine={false} minTickGap={24} />
          <YAxis tickFormatter={yTickFormat} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={Y_AXIS_W} />
          <ReferenceLine y={0} />
          {tooltip}
          {bars}
        </BarChart>
      </ChartFrame>
    </div>
  )
}
