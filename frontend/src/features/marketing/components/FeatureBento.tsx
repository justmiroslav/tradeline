import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"
import { Ico } from "@/shared/ui/Ico"

function TrendIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M3 16l5-6 4 3 7-9" />
      <path d="M4 21h16" />
    </svg>
  )
}

const FEATURES = [
  {
    icon: <Ico.Check width={15} height={15} />,
    title: "Per-symbol and per-setup P&L",
    body: "Every position is split by symbol and by setup, so your winners and your bleed stop hiding inside one number"
  },
  {
    icon: <TrendIcon />,
    title: "Equity, drawdown and win rate",
    body: "Closed positions roll into a live equity curve with the drawdown and win rate you actually traded through"
  },
  {
    icon: <Ico.Bolt width={15} height={15} />,
    title: "An honest AI read",
    body: "It weighs your edge against your leaks, checks its verdict against your real P&L and names only symbols you traded"
  }
]

export function FeatureBento() {
  return (
    <section className="px-6 sm:px-10 lg:px-14 py-16 sm:py-24 border-t border-line">
      <div className="max-w-2xl mx-auto text-center mb-10 sm:mb-12">
        <span className="mono text-[11.5px] uppercase tracking-[0.12em] text-fg-2">What you get</span>
        <h2
          className="text-[clamp(26px,4vw,40px)] font-semibold m-0 mt-3 text-fg-0"
          style={{ letterSpacing: "-0.03em", textWrap: "balance" }}
        >
          Every number computed from your trades
        </h2>
      </div>

      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4">
        {FEATURES.map(f => <Card key={f.title} icon={f.icon} title={f.title} body={f.body} />)}
      </div>
    </section>
  )
}

function Card({ icon, title, body }: { icon: ReactNode; title: string; body: string }) {
  return (
    <div className={cn("flex flex-col gap-3.5 p-6 bg-bg-1 border border-line rounded-2xl")}>
      <span className="size-9 rounded-xl bg-accent-glow text-accent inline-flex items-center justify-center shrink-0">
        {icon}
      </span>
      <h3 className="text-[15px] font-semibold text-fg-0 m-0" style={{ letterSpacing: "-0.01em" }}>{title}</h3>
      <p className="text-[13px] text-fg-2 leading-relaxed m-0">{body}</p>
    </div>
  )
}
