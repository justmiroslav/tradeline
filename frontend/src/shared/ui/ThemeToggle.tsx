import { useTheme } from "@/shared/hooks/useTheme"
import { cn } from "@/shared/lib/cn"

import { Ico } from "./Ico"

interface ThemeToggleProps {
  size?: "sm" | "md"
  className?: string
}

export function ThemeToggle({ size = "md", className }: ThemeToggleProps) {
  const { theme, toggle } = useTheme()
  const sz = size === "sm" ? "size-7" : "size-[34px]"
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      className={cn(
        "inline-flex items-center justify-center rounded-lg border border-line bg-bg-1 text-fg-1 hover:text-fg-0 hover:bg-bg-2 transition-colors",
        sz,
        className
      )}
    >
      {theme === "dark" ? <Ico.Sun width={15} height={15} /> : <Ico.Moon width={15} height={15} />}
    </button>
  )
}
