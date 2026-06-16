import { type ButtonHTMLAttributes, forwardRef, type ReactNode } from "react"

import { cn } from "@/shared/lib/cn"

import { btnClass, type BtnKind, type BtnSize } from "./btn-class"
import { Ico } from "./Ico"

interface BtnProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  kind?: BtnKind
  size?: BtnSize
  full?: boolean
  locked?: boolean
  leading?: ReactNode
  trailing?: ReactNode
  children?: ReactNode
}

export const Btn = forwardRef<HTMLButtonElement, BtnProps>(function Btn(
  { kind = "primary", size = "md", full, locked, leading, trailing, children, className, disabled, ...rest },
  ref
) {
  const isLocked = locked || disabled
  return (
    <button
      ref={ref}
      disabled={isLocked}
      className={cn(btnClass(kind, size, full, isLocked), className)}
      {...rest}
    >
      {locked && <Ico.Lock width={13} height={13} />}
      {!locked && leading}
      {children}
      {trailing}
    </button>
  )
})
