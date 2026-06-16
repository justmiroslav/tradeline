import { request } from "@/shared/lib/api"
import { buildListQuery } from "@/shared/lib/query"
import type { AnalyticsOut, ListFilters } from "@/shared/types/api"

export function getAnalyticsRequest(filters: ListFilters = {}): Promise<AnalyticsOut> {
  return request<AnalyticsOut>(`/analytics/overview${buildListQuery(filters)}`)
}
