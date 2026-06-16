import { useQuery } from "@tanstack/react-query"

import { useListResource } from "@/shared/hooks/useListResource"
import { useTokenPresence } from "@/shared/hooks/useTokenPresence"

import { type ListTradesParams, listTradesRequest, listTradeSymbolsRequest, tradesRangeRequest } from "./api"

export const tradesQueryKey = (params: ListTradesParams) => ["trades", params] as const
export const tradeSymbolsQueryKey = ["trades", "symbols"] as const
export const tradesRangeQueryKey = ["trades", "range"] as const

export function useTrades(params: ListTradesParams = {}) {
  return useListResource(tradesQueryKey(params), () => listTradesRequest(params))
}

export function useTradeSymbols() {
  const hasToken = useTokenPresence()
  return useQuery({
    queryKey: tradeSymbolsQueryKey,
    queryFn: listTradeSymbolsRequest,
    enabled: hasToken,
    staleTime: 60_000
  })
}

export function useTradesRange() {
  const hasToken = useTokenPresence()
  return useQuery({
    queryKey: tradesRangeQueryKey,
    queryFn: tradesRangeRequest,
    enabled: hasToken,
    staleTime: 60_000
  })
}
