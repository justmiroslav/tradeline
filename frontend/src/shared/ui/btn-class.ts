import { cn } from "@/shared/lib/cn"

export type BtnKind = "primary" | "secondary" | "ghost" | "outline" | "danger"
export type BtnSize = "sm" | "md" | "lg"

const sizeClass: Record<BtnSize, string> = {
  sm: "h-[30px] px-[10px] text-[12.5px] gap-1.5",
  md: "h-[38px] px-[14px] text-[13.5px] gap-2",
  lg: "h-12 px-5 text-[15px] gap-2.5"
}

const kindClass: Record<BtnKind, string> = {
  primary: "bg-accent text-accent-fg border border-transparent hover:opacity-90",
  secondary: "bg-bg-2 text-fg-0 border border-line hover:bg-bg-3",
  ghost: "bg-transparent text-fg-0 border border-transparent hover:bg-bg-2",
  outline: "bg-transparent text-fg-0 border border-line-strong hover:bg-bg-2",
  danger: "tl-btn-danger border"
}

export function btnClass(kind: BtnKind, size: BtnSize, full?: boolean, locked?: boolean): string {
  return cn(
    "inline-flex items-center justify-center rounded-lg font-medium tracking-tight whitespace-nowrap shrink-0 transition duration-150",
    sizeClass[size],
    kindClass[kind],
    full && "w-full",
    locked && "opacity-40 cursor-not-allowed"
  )
}
