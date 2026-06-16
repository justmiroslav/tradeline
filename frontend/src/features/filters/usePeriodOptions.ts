import { useMemo } from "react"

import { spanDaysFromRange, useTradesRange } from "@/features/trades"

import { periodPresets } from "./model"

export function usePeriodOptions() {
  const range = useTradesRange().data
  const periodOptions = useMemo(() => periodPresets(spanDaysFromRange(range)), [range])
  return {
    periodOptions,
    periodMin: range?.first_trade_at ?? null,
    periodMax: range?.last_trade_at ?? null
  }
}
