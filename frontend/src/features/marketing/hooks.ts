import { useQuery } from "@tanstack/react-query"

import { getMarketTickersRequest } from "./api"

export function useMarketTickers() {
  return useQuery({
    queryKey: ["market-tickers"],
    queryFn: getMarketTickersRequest,
    staleTime: 15_000,
    refetchInterval: 20_000
  })
}
