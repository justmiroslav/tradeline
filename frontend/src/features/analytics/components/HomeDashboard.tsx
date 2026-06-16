import { useMemo, useState } from "react"

import { AiInsightCard } from "@/features/ai"
import { ApiKeysOverview } from "@/features/api-keys"
import { type PeriodPreset, periodPresets, periodToAnalyticsFilters } from "@/features/filters"
import { PositionsOverview } from "@/features/positions"
import { spanDaysFromRange, useTradesRange } from "@/features/trades"
import { formatNumber, formatPercent, formatSignedUsd, num } from "@/shared/lib/format"
import { PlaceholderCard } from "@/shared/ui/PlaceholderCard"
import { QueryError } from "@/shared/ui/QueryError"
import { Segmented, type SegmentedOption } from "@/shared/ui/Segmented"

import { useAnalytics } from "../hooks"
import { EquityHero, type HeroStat } from "./EquityHero"
import { ImportingState } from "./ImportingState"

const SHORT_LABEL: Record<PeriodPreset, string> = {
  all: "All", "7d": "7D", "30d": "30D", "90d": "90D", "1y": "1Y", custom: "Custom"
}

export function HomeDashboard() {
  const [period, setPeriod] = useState<PeriodPreset>("all")
  const spanDays = spanDaysFromRange(useTradesRange().data)

  const periodOptions = useMemo<SegmentedOption<PeriodPreset>[]>(
    () => periodPresets(spanDays).map(p => ({ value: p.value, label: SHORT_LABEL[p.value] })),
    [spanDays]
  )

  const filters = useMemo(() => periodToAnalyticsFilters(period), [period])
  const query = useAnalytics(filters)

  if (query.isPending) return <PlaceholderCard hint="Loading…" />
  if (query.isError) return <QueryError message="Couldn't load your dashboard" onRetry={() => query.refetch()} />

  const a = query.data
  if (!a || (a.kpis.total_positions === 0 && a.open_exposure.count === 0 && a.incomplete_count === 0)) return <ImportingState />

  const k = a.kpis
  const maxDd = num(k.max_drawdown)
  const stats: HeroStat[] = [
    { label: "Win rate", value: formatPercent(k.win_rate) },
    { label: "Positions", value: formatNumber(k.total_positions) },
    { label: "Max drawdown", value: formatSignedUsd(-Math.abs(maxDd)), tone: maxDd ? "loss" : "neutral" }
  ]

  return (
    <div className="tl-page flex flex-col gap-4 sm:gap-5">
      <div className="grid gap-4 sm:gap-5 xl:grid-cols-12 xl:grid-rows-[auto_auto] items-start">
        <EquityHero
          className="min-w-0 xl:col-start-1 xl:col-span-8 xl:row-start-1"
          netPnl={num(k.net_pnl)}
          stats={stats}
          equity={a.equity_curve}
          height={248}
          control={<Segmented<PeriodPreset> ariaLabel="Period" size="sm" variant="flat" value={period} onChange={setPeriod} options={periodOptions} />}
        />

        <AiInsightCard className="min-w-0 xl:col-start-9 xl:col-span-4 xl:row-start-1" />

        <div className="grid gap-4 sm:gap-5 sm:grid-cols-[1.7fr_1fr] items-start min-w-0 xl:col-start-1 xl:col-span-8 xl:row-start-2">
          <PositionsOverview />
          <ApiKeysOverview />
        </div>
      </div>
    </div>
  )
}
