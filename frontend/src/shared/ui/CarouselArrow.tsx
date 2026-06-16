import { cn } from "@/shared/lib/cn"
import { Ico } from "@/shared/ui/Ico"

interface CarouselArrowProps {
  dir: "prev" | "next"
  label: string
  onClick: () => void
  disabled?: boolean
  size?: number
}

export function CarouselArrow({ dir, label, onClick, disabled, size = 24 }: CarouselArrowProps) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      style={{ width: size, height: size }}
      className={cn(
        "shrink-0 inline-flex items-center justify-center rounded-md text-fg-2 transition-colors cursor-pointer",
        "hover:bg-bg-2 hover:text-fg-0 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-fg-2"
      )}
    >
      <Ico.Chevron width={14} height={14} className={dir === "prev" ? "rotate-90" : "-rotate-90"} />
    </button>
  )
}
