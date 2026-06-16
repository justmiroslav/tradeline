import type { TradeRangeOut } from "@/shared/types/api"

export function spanDaysFromRange(range: TradeRangeOut | undefined): number {
  if (!range?.first_trade_at || !range?.last_trade_at) return 0
  const ms = new Date(range.last_trade_at).getTime() - new Date(range.first_trade_at).getTime()
  return ms > 0 ? ms / 86_400_000 : 0
}
