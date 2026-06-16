import { cn } from "@/shared/lib/cn"

const TONES = {
  accent: "border-accent/40 border-t-accent",
  onAccent: "border-accent-fg/40 border-t-accent-fg",
  muted: "border-line border-t-accent"
} as const

interface SpinnerProps {
  size?: number
  tone?: keyof typeof TONES
  className?: string
}

export function Spinner({ size = 14, tone = "accent", className }: SpinnerProps) {
  return (
    <span
      aria-hidden
      className={cn("inline-block shrink-0 rounded-full border-2 animate-tl-spin", TONES[tone], className)}
      style={{ width: size, height: size }}
    />
  )
}
