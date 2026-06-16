import { useMemo } from "react"
import { useNavigate } from "react-router-dom"

import { useApiKeys } from "@/features/api-keys"
import { collapseAllTickers, FiltersBar, isFilterActive, toAnalyticsFilters, usePeriodOptions, useScopedFilters } from "@/features/filters"
import { useTradeSymbols } from "@/features/trades"
import { formatNumber, formatPercent, formatSignedUsd, num } from "@/shared/lib/format"
import type { KpiOut, MarketType, PositionSide } from "@/shared/types/api"
import { Panel } from "@/shared/ui/Panel"
import { PlaceholderCard } from "@/shared/ui/PlaceholderCard"
import { QueryError } from "@/shared/ui/QueryError"

import { DailyPnlBars } from "../charts/DailyPnlBars"
import { useAnalytics } from "../hooks"
import { BehavioralPanel } from "./BehavioralPanel"
import { BreakdownPanel } from "./BreakdownPanel"
import { CalendarBoard } from "./CalendarBoard"
import { EquityHero, type HeroStat } from "./EquityHero"
import { ImportingState, NoTradesYet } from "./ImportingState"

function heroStats(k: KpiOut): HeroStat[] {
  const expectancy = num(k.expectancy)
  const avgWin = num(k.avg_win)
  const avgLoss = num(k.avg_loss)
  const maxDd = num(k.max_drawdown)
  return [
    { label: "Win rate", value: formatPercent(k.win_rate) },
    { label: "Profit factor", value: k.profit_factor != null ? formatNumber(k.profit_factor, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—" },
    { label: "Expectancy", value: formatSignedUsd(expectancy), tone: expectancy > 0 ? "profit" : expectancy < 0 ? "loss" : "neutral" },
    { label: "Positions", value: formatNumber(k.total_positions) },
    { label: "Avg win", value: formatSignedUsd(avgWin), tone: avgWin ? "profit" : "neutral" },
    { label: "Avg loss", value: formatSignedUsd(avgLoss), tone: avgLoss ? "loss" : "neutral" },
    { label: "Max drawdown", value: formatSignedUsd(-Math.abs(maxDd)), tone: maxDd ? "loss" : "neutral" }
  ]
}

export function AnalyticsDashboard() {
  const navigate = useNavigate()
  const { filters, setFilters, reset } = useScopedFilters("analytics")
  const positions = useScopedFilters("positions")
  const keys = useApiKeys().data ?? []
  const symbolOptions = useTradeSymbols().data ?? []
  const { periodOptions, periodMin, periodMax } = usePeriodOptions()

  const queryFilters = useMemo(
    () => toAnalyticsFilters(collapseAllTickers(filters, symbolOptions.length), filters.keys),
    [filters, symbolOptions.length]
  )

  const query = useAnalytics(queryFilters)
  const a = query.data
  const active = isFilterActive(filters, "analytics")

  const toggleTicker = (symbol: string) =>
    setFilters({ ...filters, tickers: filters.tickers.includes(symbol) ? filters.tickers.filter(t => t !== symbol) : [...filters.tickers, symbol] })

  const toggleSide = (label: string) => {
    const side = label.toLowerCase() as PositionSide
    setFilters({ ...filters, side: filters.side === side ? null : side })
  }

  const toggleMarket = (label: string) => {
    const market = label.toLowerCase() as MarketType
    setFilters({ ...filters, market: filters.market === market ? null : market })
  }

  const openDay = (iso: string) => {
    positions.setFilters({ ...filters, period: "custom", customFrom: `${iso}T00:00:00.000Z`, customTo: `${iso}T23:59:59.999Z`, status: "closed" })
    navigate("/dashboard/journal", { state: { view: "positions" } })
  }

  return (
    <div className="tl-page flex flex-col gap-4 sm:gap-5">
      <FiltersBar
        filters={filters}
        onChange={setFilters}
        active={active}
        keys={keys}
        symbolOptions={symbolOptions}
        periodOptions={periodOptions}
        periodMin={periodMin}
        periodMax={periodMax}
        showSide
        onReset={reset}
      />

      {query.isPending && !a ? (
        <PlaceholderCard hint="Loading…" />
      ) : query.isError && !a ? (
        <QueryError message="Couldn't load analytics" onRetry={() => query.refetch()} />
      ) : !a || (a.kpis.total_positions === 0 && a.open_exposure.count === 0 && a.incomplete_count === 0) ? (
        active
          ? <PlaceholderCard title="No closed positions match these filters" hint="Try widening or clearing the filters above" />
          : keys.some(k => k.syncing) ? <ImportingState /> : <NoTradesYet />
      ) : a.kpis.total_positions === 0 ? (
        <PlaceholderCard title="No closed positions yet" hint="Analytics fills in once a position closes — your open ones are in the Journal" />
      ) : (
        <div className="grid gap-4 sm:gap-5 xl:grid-cols-12 xl:grid-rows-[auto_auto] items-stretch">
          <EquityHero
            className="min-w-0 xl:col-start-1 xl:col-span-8 xl:row-start-1"
            netPnl={num(a.kpis.net_pnl)}
            stats={heroStats(a.kpis)}
            equity={a.equity_curve}
            height={236}
          />

          <Panel title="Calendar" className="min-w-0 xl:col-start-9 xl:col-span-4 xl:row-start-1 xl:row-span-2">
            <CalendarBoard daily={a.daily_pnl} onSelectDay={openDay} />
          </Panel>

          <div className="grid gap-4 sm:gap-5 sm:grid-cols-2 xl:grid-cols-[1fr_1fr_0.8fr] min-w-0 xl:col-start-1 xl:col-span-8 xl:row-start-2">
            <Panel title="Daily P&L" className="min-w-0">
              <DailyPnlBars daily={a.daily_pnl} height={170} scrollAfter={18} minBarWidth={20} />
            </Panel>
            <BreakdownPanel className="min-w-0" a={a} onToggleTicker={toggleTicker} onToggleSide={toggleSide} onToggleMarket={toggleMarket} />
            <Panel title="Behavioral" className="min-w-0">
              <BehavioralPanel duration={a.duration} averaging={a.averaging} excursion={a.excursion} />
            </Panel>
          </div>
        </div>
      )}
    </div>
  )
}
