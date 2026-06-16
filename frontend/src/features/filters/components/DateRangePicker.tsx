import { useMemo, useState } from "react"

import { cn } from "@/shared/lib/cn"
import { addMonths, dayKey, monthGrid, MONTHS, startOfMonth, WEEKDAYS } from "@/shared/lib/date"
import { Ico } from "@/shared/ui/Ico"

interface DateRangePickerProps {
  from: Date | null
  to: Date | null
  min: Date | null
  max: Date | null
  onSelect: (from: Date | null, to: Date | null) => void
}

export function DateRangePicker({ from, to, min, max, onSelect }: DateRangePickerProps) {
  const upper = max ?? new Date()
  const [view, setView] = useState(() => startOfMonth(to ?? from ?? upper))

  const cells = useMemo(() => monthGrid(view), [view])
  const minKey = min ? dayKey(min) : -Infinity
  const maxKey = dayKey(upper)
  const minMonth = min ? dayKey(startOfMonth(min)) : -Infinity
  const maxMonth = dayKey(startOfMonth(upper))
  const viewMonthKey = dayKey(view)
  const fromKey = from ? dayKey(from) : null
  const toKey = to ? dayKey(to) : null

  const canPrev = viewMonthKey > minMonth
  const canNext = viewMonthKey < maxMonth

  const shift = (months: number) => setView(addMonths(view, months))

  const pick = (day: Date) => {
    if (!from || (from && to)) {
      onSelect(day, null)
    } else if (dayKey(day) < dayKey(from)) {
      onSelect(day, null)
    } else {
      onSelect(from, day)
    }
  }

  return (
    <div className="w-[252px] select-none">
      <div className="flex items-center justify-between mb-2">
        <button
          type="button"
          aria-label="Previous month"
          disabled={!canPrev}
          onClick={() => shift(-1)}
          className="size-7 inline-flex items-center justify-center rounded-md text-fg-2 hover:bg-bg-2 hover:text-fg-0 transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent"
        >
          <Ico.Chevron width={14} height={14} className="rotate-90" />
        </button>
        <span className="text-[12.5px] font-medium text-fg-0">{MONTHS[view.getMonth()]} {view.getFullYear()}</span>
        <button
          type="button"
          aria-label="Next month"
          disabled={!canNext}
          onClick={() => shift(1)}
          className="size-7 inline-flex items-center justify-center rounded-md text-fg-2 hover:bg-bg-2 hover:text-fg-0 transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent"
        >
          <Ico.Chevron width={14} height={14} className="-rotate-90" />
        </button>
      </div>

      <div className="grid grid-cols-7 mb-1">
        {WEEKDAYS.map(w => (
          <span key={w} className="h-6 inline-flex items-center justify-center text-[10px] uppercase tracking-[0.04em] text-fg-3">{w}</span>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-y-1">
        {cells.map(day => {
          const k = dayKey(day)
          const inMonth = day.getMonth() === view.getMonth()
          const disabled = k < minKey || k > maxKey
          const isStart = k === fromKey
          const isEnd = k === toKey
          const isEndpoint = isStart || isEnd
          const inRange = fromKey != null && toKey != null && k > fromKey && k < toKey
          const single = (isStart && isEnd) || (isStart && toKey === null)

          return (
            <button
              key={k}
              type="button"
              disabled={disabled}
              onClick={() => pick(day)}
              className={cn(
                "h-8 text-[12px] mono tnum inline-flex items-center justify-center transition-colors cursor-pointer",
                single ? "rounded-md" : isStart ? "rounded-l-md" : isEnd ? "rounded-r-md" : !inRange && "rounded-md",
                !disabled && !isEndpoint && !inRange && (inMonth ? "text-fg-1 hover:bg-bg-2" : "text-fg-3 hover:bg-bg-2"),
                disabled && "opacity-25 cursor-not-allowed",
                inRange && "tl-cal-range text-fg-0 font-medium",
                isEndpoint && "tl-cal-edge font-semibold"
              )}
            >
              {day.getDate()}
            </button>
          )
        })}
      </div>
    </div>
  )
}
