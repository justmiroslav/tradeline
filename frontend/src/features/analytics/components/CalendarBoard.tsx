import { useEffect, useMemo, useRef, useState } from "react"

import { cn } from "@/shared/lib/cn"
import { addMonths, dayKey, isoDate, monthGrid, monthKey, MONTHS, parseIsoDate, startOfMonth, WEEKDAYS } from "@/shared/lib/date"
import { formatDayFull, formatSignedUsd, num, pnlToneClass, toneClass } from "@/shared/lib/format"
import type { DailyPnl } from "@/shared/types/api"
import { CarouselArrow } from "@/shared/ui/CarouselArrow"

type Tone = "neutral" | "profit" | "loss"

interface DayData {
  net: number
  count: number
}

interface MonthSummary {
  total: number
  days: number
  wins: number
  best: number | null
}

interface CalendarBoardProps {
  daily: DailyPnl[]
  onSelectDay: (iso: string) => void
}

export function CalendarBoard({ daily, onSelectDay }: CalendarBoardProps) {
  const dayMap = useMemo(() => {
    const m = new Map<string, DayData>()
    for (const d of daily) m.set(d.date, { net: num(d.net_pnl), count: d.count })
    return m
  }, [daily])

  const minMonth = useMemo(() => startOfMonth(daily.length ? parseIsoDate(daily[0].date) : new Date()), [daily])
  const maxMonth = useMemo(() => startOfMonth(daily.length ? parseIsoDate(daily[daily.length - 1].date) : new Date()), [daily])
  const [view, setView] = useState(maxMonth)

  const lastMaxKey = useRef(monthKey(maxMonth))
  useEffect(() => {
    const k = monthKey(maxMonth)
    if (k !== lastMaxKey.current) { lastMaxKey.current = k; setView(maxMonth) }
  }, [maxMonth])

  const cells = useMemo(() => monthGrid(view), [view])
  const viewKey = monthKey(view)
  const todayKey = dayKey(new Date())
  const firstKey = daily.length ? daily[0].date : null

  const { maxAbs, summary } = useMemo(() => {
    let mx = 0, total = 0, days = 0, wins = 0
    let best: number | null = null
    for (const cell of cells) {
      if (cell.getMonth() !== view.getMonth()) continue
      const d = dayMap.get(isoDate(cell))
      if (!d) continue
      mx = Math.max(mx, Math.abs(d.net))
      total += d.net
      days += 1
      if (d.net > 0) wins += 1
      best = best === null ? d.net : Math.max(best, d.net)
    }
    return { maxAbs: mx, summary: { total, days, wins, best } as MonthSummary }
  }, [cells, view, dayMap])

  const canPrev = viewKey > monthKey(minMonth)
  const canNext = viewKey < monthKey(maxMonth)
  const shift = (months: number) => setView(addMonths(view, months))

  return (
    <div className="w-full flex-1 min-h-0 flex flex-col gap-3">
      <div className="flex items-center justify-center gap-4">
        <CarouselArrow dir="prev" label="Previous month" disabled={!canPrev} onClick={() => shift(-1)} size={28} />
        <span className="text-[13.5px] font-medium text-fg-0 w-[140px] text-center">{MONTHS[view.getMonth()]} {view.getFullYear()}</span>
        <CarouselArrow dir="next" label="Next month" disabled={!canNext} onClick={() => shift(1)} size={28} />
      </div>

      <div key={viewKey} className="grid grid-cols-7 grid-rows-[auto_repeat(6,minmax(0,1fr))] gap-1 flex-1 min-h-[280px] animate-tl-fade-soft">
        {WEEKDAYS.map(w => (
          <span key={w} className="inline-flex items-center justify-center text-[10px] uppercase tracking-[0.05em] text-fg-3">{w}</span>
        ))}
        {cells.map(cell => {
          const iso = isoDate(cell)
          const inMonth = cell.getMonth() === view.getMonth()
          const outOfRange = dayKey(cell) > todayKey || (firstKey !== null && iso < firstKey)
          const data = inMonth && !outOfRange ? dayMap.get(iso) : undefined
          return <DayCell key={iso} day={cell.getDate()} iso={iso} inMonth={inMonth} outOfRange={outOfRange} data={data} maxAbs={maxAbs} onSelect={onSelectDay} />
        })}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <SummaryStat label="Month P&L" value={formatSignedUsd(summary.total)} tone={summary.total > 0 ? "profit" : summary.total < 0 ? "loss" : "neutral"} />
        <SummaryStat label="Trading days" value={String(summary.days)} tone="neutral" />
        <SummaryStat label="Win days" value={`${summary.wins}/${summary.days}`} tone="neutral" />
        <SummaryStat label="Best day" value={summary.best === null ? "—" : formatSignedUsd(summary.best)} tone={summary.best !== null && summary.best > 0 ? "profit" : "neutral"} />
      </div>
    </div>
  )
}

function SummaryStat({ label, value, tone }: { label: string; value: string; tone: Tone }) {
  return (
    <div className="rounded-lg border border-line bg-bg-2 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-fg-3">{label}</div>
      <div className={cn("mono tnum text-[13.5px] font-semibold mt-0.5", toneClass(tone))}>{value}</div>
    </div>
  )
}

function DayCell({ day, iso, inMonth, outOfRange, data, maxAbs, onSelect }: { day: number; iso: string; inMonth: boolean; outOfRange: boolean; data: DayData | undefined; maxAbs: number; onSelect: (iso: string) => void }) {
  return (
    <button
      type="button"
      disabled={!data}
      onClick={() => data && onSelect(iso)}
      title={data ? `${formatDayFull(iso)} · ${data.count} ${data.count === 1 ? "position" : "positions"}` : undefined}
      className={cn(
        "min-h-0 rounded-md p-1.5 flex flex-col justify-between text-left border border-transparent transition-colors overflow-hidden",
        !inMonth
          ? "opacity-40"
          : outOfRange
            ? "bg-bg-2/50"
            : data
              ? cn(tintClass(data.net, maxAbs), "cursor-pointer hover:border-line-strong")
              : "tl-day-out cursor-default"
      )}
    >
      <span className="text-[10px] mono tnum text-fg-3 leading-none">{day}</span>
      {data && (
        <span className={cn("mono tnum text-[11px] font-semibold leading-none", pnlToneClass(data.net))}>
          {formatSignedUsd(data.net)}
        </span>
      )}
    </button>
  )
}

function tintClass(net: number, maxAbs: number): string {
  const ratio = maxAbs > 0 ? Math.abs(net) / maxAbs : 0
  const lvl = ratio < 0.34 ? 1 : ratio < 0.67 ? 2 : 3
  return net >= 0 ? `tl-day-p${lvl}` : `tl-day-l${lvl}`
}
