import { useState } from "react"

import { cn } from "@/shared/lib/cn"
import { formatPercent, formatSignedUsd, num, pnlToneClass } from "@/shared/lib/format"
import type { AveragingStat, DurationStat, ExcursionStat } from "@/shared/types/api"
import { CarouselArrow } from "@/shared/ui/CarouselArrow"
import { Tooltip } from "@/shared/ui/Tooltip"

interface BehavioralPanelProps {
  duration: DurationStat
  averaging: AveragingStat
  excursion: ExcursionStat
}

interface StatRow {
  label: string
  hint: string
  value: string
  tone?: number
}

interface Slide {
  title: string
  hint: string
  stats: StatRow[]
}

export function BehavioralPanel({ duration, averaging, excursion }: BehavioralPanelProps) {
  const avgNet = num(averaging.averaged_down_net)
  const restNet = num(averaging.rest_net)

  const slides: Slide[] = [
    {
      title: "Hold time",
      hint: "How long positions stay open from entry to close, split by outcome",
      stats: [
        { label: "Avg win", hint: "Mean time winning positions stayed open", value: fmtDuration(duration.avg_win_minutes) },
        { label: "Avg loss", hint: "Mean time losing positions stayed open", value: fmtDuration(duration.avg_loss_minutes) },
        { label: "Median win", hint: "Middle hold time of winning positions", value: fmtDuration(duration.median_win_minutes) },
        { label: "Median loss", hint: "Middle hold time of losing positions", value: fmtDuration(duration.median_loss_minutes) }
      ]
    },
    {
      title: "Averaging down",
      hint: "Positions where you added to a loser vs all other positions",
      stats: [
        { label: "Averaged", hint: "Count of averaged-down positions and their win rate", value: `${averaging.averaged_down_count} · ${formatPercent(averaging.averaged_down_win_rate)}` },
        { label: "Averaged net", hint: "Total net P&L of averaged-down positions", value: formatSignedUsd(avgNet), tone: avgNet },
        { label: "Rest", hint: "Count of all other positions and their win rate", value: `${averaging.rest_count} · ${formatPercent(averaging.rest_win_rate)}` },
        { label: "Rest net", hint: "Total net P&L of non-averaged positions", value: formatSignedUsd(restNet), tone: restNet }
      ]
    },
    {
      title: "Excursion",
      hint: "Peak unrealized profit (MFE) and worst drawdown (MAE) reached inside a position, as % of entry price",
      stats: [
        { label: "Avg MFE", hint: "Average peak unrealized profit reached, as % of entry price", value: formatPercent(excursion.avg_mfe) },
        { label: "Avg MAE", hint: "Average worst drawdown reached, as % of entry price", value: formatPercent(excursion.avg_mae) },
        { label: "Winner MFE", hint: "How far winners ran in your favor, as % of entry price", value: formatPercent(excursion.avg_winner_mfe) },
        { label: "Loser MAE", hint: "How deep losers went against you, as % of entry price", value: formatPercent(excursion.avg_loser_mae) }
      ]
    }
  ]

  const [idx, setIdx] = useState(0)
  const slide = slides[idx]
  const go = (d: number) => setIdx((idx + d + slides.length) % slides.length)

  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="flex items-center justify-between gap-2">
        <CarouselArrow dir="prev" label="Previous metric" onClick={() => go(-1)} />
        <Tooltip content={slide.hint} side="top" align="center">
          <span className="text-[11.5px] uppercase tracking-[0.06em] text-fg-1 font-medium cursor-help text-center truncate">{slide.title}</span>
        </Tooltip>
        <CarouselArrow dir="next" label="Next metric" onClick={() => go(1)} />
      </div>

      <div key={idx} className="flex-1 flex flex-col justify-center gap-2.5 animate-tl-fade-soft">
        {slide.stats.map(s => <Stat key={s.label} {...s} />)}
      </div>

      <div className="flex items-center justify-center gap-1.5">
        {slides.map((s, i) => (
          <button
            key={s.title}
            type="button"
            aria-label={`Show ${s.title}`}
            onClick={() => setIdx(i)}
            className={cn("h-1.5 rounded-full transition-all cursor-pointer", i === idx ? "w-4 bg-accent" : "w-1.5 bg-line-strong hover:bg-fg-3")}
          />
        ))}
      </div>
    </div>
  )
}

function Stat({ label, value, tone, hint }: StatRow) {
  return (
    <div className="flex items-baseline justify-between gap-3 text-[12.5px]">
      <Tooltip content={hint} side="top" align="start">
        <span className="text-fg-3 cursor-help">{label}</span>
      </Tooltip>
      <span className={cn("mono tnum font-medium", pnlToneClass(tone ?? 0))}>{value}</span>
    </div>
  )
}

function fmtDuration(minutes: number | null): string {
  if (minutes == null) return "—"
  if (minutes < 60) return `${Math.round(minutes)}m`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ${Math.round(minutes % 60)}m`
  const days = Math.floor(hours / 24)
  return `${days}d ${hours % 24}h`
}
