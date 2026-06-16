import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"

export interface SegmentedOption<T extends string> {
  value: T
  label: ReactNode
}

interface SegmentedProps<T extends string> {
  value: T
  onChange: (value: T) => void
  options: SegmentedOption<T>[]
  ariaLabel?: string
  size?: "xs" | "sm" | "md"
  variant?: "pill" | "flat"
  className?: string
}

export function Segmented<T extends string>({ value, onChange, options, ariaLabel, size = "md", variant = "pill", className }: SegmentedProps<T>) {
  const count = options.length
  const activeIndex = Math.max(0, options.findIndex(o => o.value === value))
  const pad = size === "md" ? 4 : 3
  const radius = variant === "flat" ? "rounded-lg" : "rounded-full"
  const radiusInner = variant === "flat" ? "rounded-md" : "rounded-full"

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      className={cn("relative inline-grid bg-bg-0 border border-line", radius, size === "md" ? "p-1" : "p-[3px]", className)}
      style={{ gridTemplateColumns: `repeat(${count}, minmax(0, 1fr))` }}
    >
      <span
        aria-hidden
        className={cn("absolute bg-bg-3 shadow-card pointer-events-none", radiusInner)}
        style={{
          top: pad,
          bottom: pad,
          left: pad,
          width: `calc((100% - ${pad * 2}px) / ${count})`,
          transform: `translateX(${activeIndex * 100}%)`,
          transition: "transform 360ms cubic-bezier(0.16, 1, 0.3, 1)"
        }}
      />
      {options.map(o => {
        const active = o.value === value
        return (
          <button
            key={o.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(o.value)}
            className={cn(
              "relative z-10 inline-flex items-center justify-center font-medium whitespace-nowrap cursor-pointer transition-colors duration-200",
              radiusInner,
              size === "xs" ? "px-1.5 py-0.5 text-[10px]" : size === "sm" ? "px-2 py-0.5 text-[10.5px]" : "px-3.5 py-1.5 text-[12.5px]",
              active ? "text-fg-0" : "text-fg-2 hover:text-fg-1"
            )}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}
