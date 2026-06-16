import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react"

import { cn } from "@/shared/lib/cn"

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  trailing?: ReactNode
  invalid?: boolean
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { trailing, invalid, className, ...rest },
  ref
) {
  return (
    <span className="relative flex items-center">
      <input
        ref={ref}
        className={cn(
          "w-full h-10 rounded-lg bg-bg-2 border text-[14px] text-fg-0 placeholder:text-fg-3 outline-none transition-colors",
          "focus:border-accent",
          invalid ? "border-loss" : "border-line",
          trailing ? "pr-9.5 pl-3" : "px-3",
          className
        )}
        {...rest}
      />
      {trailing && (
        <span className="absolute right-2.5 inline-flex text-fg-2 pointer-events-none">
          {trailing}
        </span>
      )}
    </span>
  )
})
