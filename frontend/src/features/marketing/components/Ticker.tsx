import { cn } from "@/shared/lib/cn"

import { useMarketTickers } from "../hooks"

const SECONDS_PER_ITEM = 4.2

function fmtPrice(px: number): string {
  if (px >= 1) return px.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return px.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 })
}

export function Ticker() {
  const items = useMarketTickers().data ?? []

  return (
    <div
      className="border-y border-line bg-bg-1 overflow-hidden relative min-h-[43px]"
      style={{
        maskImage: "linear-gradient(90deg, transparent 0%, black 5%, black 95%, transparent 100%)",
        WebkitMaskImage: "linear-gradient(90deg, transparent 0%, black 5%, black 95%, transparent 100%)"
      }}
      aria-label="Live tickers"
    >
      {items.length > 0 && (
        <div
          className="flex items-center w-max animate-tl-marquee"
          style={{ animationDuration: `${items.length * SECONDS_PER_ITEM}s` }}
          role="marquee"
        >
          {[...items, ...items].map((t, i) => (
            <div
              key={i}
              className="flex items-center gap-2.75 px-5.5 py-3.25 border-r border-line shrink-0"
            >
              <span className="mono text-[12px] text-fg-2 font-medium">{t.symbol}</span>
              <span className="mono tnum text-[13px] text-fg-0 font-medium">{fmtPrice(t.price)}</span>
              <span
                className={cn(
                  "mono tnum text-[11.5px]",
                  t.change_pct >= 0 ? "text-profit" : "text-loss"
                )}
              >
                {t.change_pct >= 0 ? "▲" : "▼"} {Math.abs(t.change_pct).toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
