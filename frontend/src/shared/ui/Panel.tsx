import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"

interface PanelProps {
  title?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
}

export function Panel({ title, action, children, className }: PanelProps) {
  return (
    <section className={cn("rounded-xl border border-line bg-bg-1 shadow-card p-4 sm:p-5 flex flex-col", className)}>
      {(title || action) && (
        <div className="flex items-center justify-between gap-3 mb-3 min-h-7">
          {title && <h2 className="text-[13px] font-semibold text-fg-0 m-0 whitespace-nowrap shrink-0">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  )
}
