import { cn } from "@/shared/lib/cn"

interface AvatarProps {
  initial: string
  src?: string | null
  size?: number
  className?: string
}

export function Avatar({ initial, src, size = 28, className }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt=""
        width={size}
        height={size}
        referrerPolicy="no-referrer"
        className={cn("rounded-full object-cover shrink-0", className)}
        style={{ width: size, height: size }}
      />
    )
  }

  const fontSize = Math.round(size * 0.42)
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-full bg-accent-glow text-accent font-semibold shrink-0",
        className
      )}
      style={{ width: size, height: size, fontSize }}
      aria-hidden
    >
      {initial}
    </span>
  )
}
