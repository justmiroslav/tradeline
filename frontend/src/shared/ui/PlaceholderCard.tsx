import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"

interface PlaceholderCardProps {
  title?: string
  hint?: string
  children?: ReactNode
  className?: string
}

export function PlaceholderCard({ title, hint, children, className }: PlaceholderCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-line bg-bg-1 p-5 shadow-card",
        className
      )}
    >
      {title && (
        <div className="text-[11.5px] uppercase tracking-[0.08em] text-fg-2 mb-2.5">
          {title}
        </div>
      )}
      {children}
      {hint && <div className="text-[12.5px] text-fg-2">{hint}</div>}
    </div>
  )
}
