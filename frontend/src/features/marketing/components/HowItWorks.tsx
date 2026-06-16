import { lazy, type ReactNode, Suspense } from "react"

import { PnlCell, SidePill, SymbolCell } from "@/features/journal/cells"
import type { EquityPoint, Exchange } from "@/shared/types/api"
import { ExchangeMark, type ExchangeName } from "@/shared/ui/ExchangeMark"
import { Input } from "@/shared/ui/Input"
import { Pill } from "@/shared/ui/Pill"

const EquityCurve = lazy(() =>
  import("@/features/analytics/charts/EquityCurve").then(m => ({ default: m.EquityCurve }))
)

const EXCHANGES: ExchangeName[] = ["binance", "bybit", "okx", "bitget"]

const TRADES: { exchange: Exchange; symbol: string; side: string; pnl: number }[] = [
  { exchange: "binance", symbol: "BTCUSDT", side: "long", pnl: 612.4 },
  { exchange: "bybit", symbol: "ETHUSDT", side: "long", pnl: 248.1 },
  { exchange: "okx", symbol: "SOLUSDT", side: "short", pnl: -86.5 },
  { exchange: "bitget", symbol: "BNBUSDT", side: "long", pnl: 154 }
]

const EQUITY: EquityPoint[] = [
  { time: "2026-05-08", equity: "0" },
  { time: "2026-05-09", equity: "85" },
  { time: "2026-05-10", equity: "160" },
  { time: "2026-05-11", equity: "120" },
  { time: "2026-05-12", equity: "235" },
  { time: "2026-05-13", equity: "190" },
  { time: "2026-05-14", equity: "110" },
  { time: "2026-05-15", equity: "270" },
  { time: "2026-05-16", equity: "360" },
  { time: "2026-05-17", equity: "300" },
  { time: "2026-05-18", equity: "430" },
  { time: "2026-05-19", equity: "390" },
  { time: "2026-05-20", equity: "540" },
  { time: "2026-05-21", equity: "470" },
  { time: "2026-05-22", equity: "620" },
  { time: "2026-05-23", equity: "700" },
  { time: "2026-05-24", equity: "600" },
  { time: "2026-05-25", equity: "740" },
  { time: "2026-05-26", equity: "690" },
  { time: "2026-05-27", equity: "900" },
  { time: "2026-05-28", equity: "1010" },
  { time: "2026-05-29", equity: "940" },
  { time: "2026-05-30", equity: "1120" },
  { time: "2026-05-31", equity: "1280" },
  { time: "2026-06-01", equity: "1340" }
]

export function HowItWorks() {
  return (
    <section className="px-6 sm:px-10 lg:px-14 py-16 sm:py-24 border-t border-line">
      <div className="mb-10.5 text-center">
        <span className="mono text-[11.5px] uppercase tracking-[0.12em] text-fg-2">How it works</span>
        <h2
          className="text-[clamp(26px,4vw,40px)] font-semibold m-0 mt-2 text-fg-0"
          style={{ letterSpacing: "-0.03em", textWrap: "balance" }}
        >
          Three minutes to a live dashboard
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Step
          n="01"
          title="Connect a read-only key"
          hint="Add a key from any of the four exchanges. It stays read-only and encrypted, so trading and withdrawals are never possible"
        >
          <div className="flex items-center gap-2">
            {EXCHANGES.map(name => <ExchangeMark key={name} name={name} size={26} />)}
          </div>
          <Input readOnly value="3f9a••••••••••••••d2c7" className="cursor-default" aria-label="API key preview" />
          <Pill tone="profit" dot className="w-fit">read-only · withdraw blocked</Pill>
        </Step>

        <Step
          n="02"
          title="Matched into positions"
          hint="Every trade across spot and perps is imported and matched into closed positions, automatically"
        >
          <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
            {TRADES.map(f => (
              <li
                key={f.symbol}
                className="flex items-center gap-2 bg-bg-0 border border-line rounded-lg px-2.5 py-2 text-[12.5px]"
              >
                <span className="flex-1 min-w-0"><SymbolCell exchange={f.exchange} symbol={f.symbol} /></span>
                <SidePill side={f.side} />
                <span className="min-w-15 text-right"><PnlCell value={f.pnl} /></span>
              </li>
            ))}
          </ul>
        </Step>

        <Step
          n="03"
          title="Your analytics, live"
          hint="Closed positions roll into a live equity curve, win-rate and drawdown KPIs and a P&L calendar"
        >
          <div className="flex items-baseline justify-between">
            <span className="text-[11px] text-fg-2">Net P&amp;L · 30d</span>
            <span className="mono tnum text-[20px] font-semibold text-profit">+$1,340</span>
          </div>
          <div className="h-31">
            <Suspense fallback={<div className="h-full rounded-lg bg-bg-0 border border-line animate-tl-pulse" />}>
              <EquityCurve points={EQUITY} height={124} />
            </Suspense>
          </div>
        </Step>
      </div>
    </section>
  )
}

interface StepProps {
  n: string
  title: string
  hint: string
  children: ReactNode
}

function Step({ n, title, hint, children }: StepProps) {
  return (
    <div className="p-7 bg-bg-1 border border-line rounded-2xl flex flex-col gap-5">
      <span className="mono text-[11.5px] tracking-widest text-accent">STEP {n}</span>
      <div className="flex flex-col gap-2.5">{children}</div>
      <div className="mt-auto">
        <div className="text-[16px] font-semibold text-fg-0" style={{ letterSpacing: "-0.01em" }}>{title}</div>
        <p className="text-[12.5px] text-fg-2 leading-relaxed m-0 mt-1.5">{hint}</p>
      </div>
    </div>
  )
}
