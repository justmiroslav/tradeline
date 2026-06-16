import { cn } from "@/shared/lib/cn"

export type ExchangeName = "binance" | "bybit" | "okx" | "bitget"

interface ExchangeMarkProps {
  name: ExchangeName
  size?: number
  className?: string
}

const ICONS: Record<ExchangeName, string> = {
  binance: "/icons/binance.jpg",
  bybit: "/icons/bybit.png",
  okx: "/icons/okx.jpg",
  bitget: "/icons/bitget.jpg"
}

const LABELS: Record<ExchangeName, string> = {
  binance: "Binance",
  bybit: "Bybit",
  okx: "OKX",
  bitget: "Bitget"
}

export function ExchangeMark({ name, size = 24, className }: ExchangeMarkProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center shrink-0 overflow-hidden rounded-md bg-bg-2",
        className
      )}
      style={{ width: size, height: size }}
    >
      <img
        src={ICONS[name]}
        alt={LABELS[name]}
        width={size}
        height={size}
        loading="eager"
        decoding="async"
        draggable={false}
        className="w-full h-full object-cover select-none"
      />
    </span>
  )
}
