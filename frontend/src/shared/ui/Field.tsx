import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"

interface FieldProps {
  label: string
  htmlFor?: string
  hint?: ReactNode
  error?: string
  children: ReactNode
  className?: string
}

export function Field({ label, htmlFor, hint, error, children, className }: FieldProps) {
  return (
    <label htmlFor={htmlFor} className={cn("flex flex-col gap-1.75", className)}>
      <span className="text-[12.5px] font-medium text-fg-1">{label}</span>
      {children}
      {error && <span className="text-[11.5px] text-loss">{error}</span>}
      {!error && hint && <span className="text-[11.5px] text-fg-2">{hint}</span>}
    </label>
  )
}
