import { useListResource } from "@/shared/hooks/useListResource"

import { type ListPositionsParams, listPositionsRequest } from "./api"

export const positionsQueryKey = (params: ListPositionsParams) => ["positions", params] as const

export function usePositions(params: ListPositionsParams = {}) {
  return useListResource(positionsQueryKey(params), () => listPositionsRequest(params))
}
