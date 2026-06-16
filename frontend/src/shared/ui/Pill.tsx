import type { CSSProperties, ReactNode } from "react"

import { cn } from "@/shared/lib/cn"

export type PillTone = "neutral" | "profit" | "loss" | "accent" | "warn"

interface PillProps {
  tone?: PillTone
  children: ReactNode
  dot?: "live" | true
  className?: string
  style?: CSSProperties
}

const toneClass: Record<PillTone, string> = {
  neutral: "bg-bg-3 text-fg-1",
  profit: "bg-profit-bg text-profit",
  loss: "bg-loss-bg text-loss",
  accent: "bg-accent-glow text-accent",
  warn: "bg-warn-bg text-warn"
}

export function Pill({ tone = "neutral", children, dot, className, style }: PillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.75 text-[11.5px] font-medium whitespace-nowrap",
        toneClass[tone],
        className
      )}
      style={style}
    >
      {dot && (
        <span
          className={cn(
            "size-1.5 rounded-full bg-current",
            dot === "live" && "animate-tl-pulse"
          )}
        />
      )}
      {children}
    </span>
  )
}
