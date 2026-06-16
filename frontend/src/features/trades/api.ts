import { downloadFile, request } from "@/shared/lib/api"
import { buildListQuery } from "@/shared/lib/query"
import type { ListFilters, TradeListOut, TradeRangeOut } from "@/shared/types/api"

export interface ListTradesParams extends ListFilters {
  page?: number
  size?: number
}

export function listTradesRequest(params: ListTradesParams = {}): Promise<TradeListOut> {
  return request<TradeListOut>(`/trades/${buildListQuery(params)}`)
}

export function listTradeSymbolsRequest(): Promise<string[]> {
  return request<string[]>("/trades/symbols")
}

export function tradesRangeRequest(): Promise<TradeRangeOut> {
  return request<TradeRangeOut>("/trades/range")
}

export function exportTradesCsv(filters: ListFilters): Promise<void> {
  return downloadFile(`/trades/export${buildListQuery(filters)}`, "trades.csv")
}
