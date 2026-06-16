import { downloadFile, request } from "@/shared/lib/api"
import { buildListQuery } from "@/shared/lib/query"
import type { ListFilters, PositionListOut, PositionStatus } from "@/shared/types/api"

export interface ListPositionsParams extends ListFilters {
  status?: PositionStatus
  page?: number
  size?: number
}

export function listPositionsRequest(params: ListPositionsParams = {}): Promise<PositionListOut> {
  return request<PositionListOut>(`/positions/${buildListQuery(params)}`)
}

export function exportPositionsCsv(params: ListPositionsParams): Promise<void> {
  return downloadFile(`/positions/export${buildListQuery(params)}`, "positions.csv")
}
