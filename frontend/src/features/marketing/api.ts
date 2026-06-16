import { request } from "@/shared/lib/api"
import type { MarketTickerOut } from "@/shared/types/api"

export function getMarketTickersRequest(): Promise<MarketTickerOut[]> {
  return request<MarketTickerOut[]>("/market/tickers", { auth: false })
}
