import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, type TooltipProps } from "recharts"

import { useChartColors, useReducedMotion } from "./chart-theme"
import { ChartTooltip } from "./ChartTooltip"

interface Slice {
  key: string
  value: number
}

interface PieChartTLProps {
  data: Slice[]
  tone: "profit" | "loss"
  valueFormat: (value: number) => string
  height?: number
  emptyHint?: string
}

export function PieChartTL({ data, tone, valueFormat, height = 184, emptyHint = "No data" }: PieChartTLProps) {
  const c = useChartColors()
  const noAnim = useReducedMotion()
  const pal = tone === "profit" ? c.pieProfit : c.pieLoss
  const total = data.reduce((sum, d) => sum + d.value, 0)
  const colorAt = (key: string, i: number) => key === "Others" ? c.axis : pal[i % pal.length]

  if (data.length === 0 || total === 0) {
    return <div style={{ height }} className="flex items-center justify-center text-[12.5px] text-fg-3">{emptyHint}</div>
  }

  return (
    <div className="flex items-center gap-4">
      <div style={{ width: height, height }} className="shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="key" innerRadius="58%" outerRadius="92%" paddingAngle={1.5} stroke="none" isAnimationActive={!noAnim}>
              {data.map((d, i) => <Cell key={i} fill={colorAt(d.key, i)} />)}
            </Pie>
            <Tooltip
              cursor={false}
              content={(p: TooltipProps<number, string>) => {
                const slice = p.payload?.[0]
                if (!p.active || !slice) return null
                const name = String(slice.name)
                return <ChartTooltip label={name} rows={[{ color: colorAt(name, data.findIndex(d => d.key === name)), text: valueFormat(slice.value as number) }]} />
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="flex-1 min-w-0 flex flex-col gap-1.5 text-[12px]">
        {data.map((d, i) => (
          <li key={d.key} className="flex items-center gap-2">
            <span className="size-2.5 rounded-sm shrink-0" style={{ background: colorAt(d.key, i) }} />
            <span className="truncate flex-1 min-w-0 text-fg-1">{d.key}</span>
            <span className="mono tnum text-fg-2 shrink-0">{Math.round((d.value / total) * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
