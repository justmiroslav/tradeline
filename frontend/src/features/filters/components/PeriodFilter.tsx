import * as DropdownMenu from "@radix-ui/react-dropdown-menu"
import { useState } from "react"

import { cn } from "@/shared/lib/cn"
import { formatDateCompact } from "@/shared/lib/format"
import { Ico } from "@/shared/ui/Ico"

import type { PeriodPreset } from "../model"
import { DateRangePicker } from "./DateRangePicker"
import { FILTER_TRIGGER_BASE } from "./filterTrigger"

interface PeriodFilterProps {
  period: PeriodPreset
  customFrom: string | null
  customTo: string | null
  presets: { value: PeriodPreset; label: string }[]
  min: string | null
  max: string | null
  onPreset: (p: PeriodPreset) => void
  onCustom: (fromIso: string, toIso: string) => void
}

const PERIOD_LABELS: Record<Exclude<PeriodPreset, "custom">, string> = {
  all: "All time", "7d": "Last 7 days", "30d": "Last 30 days", "90d": "Last 90 days", "1y": "Last year"
}

export function PeriodFilter({ period, customFrom, customTo, presets, min, max, onPreset, onCustom }: PeriodFilterProps) {
  const [open, setOpen] = useState(false)
  const [draftFrom, setDraftFrom] = useState<Date | null>(null)
  const [draftTo, setDraftTo] = useState<Date | null>(null)

  const isCustom = period === "custom" && customFrom != null && customTo != null
  const triggerLabel = period === "custom" && customFrom && customTo
    ? `${formatDateCompact(new Date(customFrom))} – ${formatDateCompact(new Date(customTo))}`
    : PERIOD_LABELS[period === "custom" ? "all" : period]

  const handleOpen = (next: boolean) => {
    if (next) {
      setDraftFrom(customFrom ? new Date(customFrom) : null)
      setDraftTo(customTo ? new Date(customTo) : null)
    }
    setOpen(next)
  }

  const choosePreset = (p: PeriodPreset) => {
    onPreset(p)
    setOpen(false)
  }

  const applyCustom = () => {
    if (!draftFrom || !draftTo) return
    const start = new Date(draftFrom); start.setHours(0, 0, 0, 0)
    const end = new Date(draftTo); end.setHours(23, 59, 59, 999)
    onCustom(start.toISOString(), end.toISOString())
    setOpen(false)
  }

  const draftLabel = draftFrom
    ? draftTo
      ? `${formatDateCompact(draftFrom)} – ${formatDateCompact(draftTo)}`
      : `${formatDateCompact(draftFrom)} – …`
    : "Pick a start and end day"

  return (
    <DropdownMenu.Root open={open} onOpenChange={handleOpen}>
      <DropdownMenu.Trigger
        aria-label="Filter by period"
        className={cn(
          FILTER_TRIGGER_BASE,
          period !== "all" ? "text-accent bg-accent-glow" : "text-fg-2 hover:text-fg-0 hover:bg-bg-2"
        )}
      >
        <Ico.Calendar width={11} height={11} className="text-fg-3" />
        <span className="whitespace-nowrap">{triggerLabel}</span>
        <Ico.Chevron width={11} height={11} className="text-fg-3 group-data-[state=open]:rotate-180 transition-transform" />
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          sideOffset={6}
          className="rounded-lg border border-line bg-bg-1 shadow-pop z-50 p-1.5 w-[280px]"
        >
          <div className="flex flex-col">
            {presets.map(p => (
              <button
                key={p.value}
                type="button"
                onClick={() => choosePreset(p.value)}
                className={cn(
                  "flex items-center gap-2 px-2.5 py-2 rounded-md text-[12.5px] outline-none cursor-pointer hover:bg-bg-2 transition-colors text-left",
                  period === p.value ? "text-fg-0" : "text-fg-1"
                )}
              >
                <span className="flex-1">{p.label}</span>
                {period === p.value && <Ico.Check width={13} height={13} className="text-accent shrink-0" />}
              </button>
            ))}
          </div>

          <div className="mt-1.5 pt-2.5 border-t border-line px-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10.5px] uppercase tracking-[0.08em] text-fg-3 font-medium">Custom range</span>
              {isCustom && <Ico.Check width={13} height={13} className="text-accent" />}
            </div>
            <DateRangePicker
              from={draftFrom}
              to={draftTo}
              min={min ? new Date(min) : null}
              max={max ? new Date(max) : null}
              onSelect={(f, t) => { setDraftFrom(f); setDraftTo(t) }}
            />
            <div className="flex items-center justify-between gap-2 mt-2.5">
              <span className="text-[11px] text-fg-2 mono tnum truncate">{draftLabel}</span>
              <button
                type="button"
                onClick={applyCustom}
                disabled={!draftFrom || !draftTo}
                className="shrink-0 h-7 px-3 rounded-md text-[12px] font-medium bg-accent text-accent-fg transition-opacity cursor-pointer hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Apply
              </button>
            </div>
          </div>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
