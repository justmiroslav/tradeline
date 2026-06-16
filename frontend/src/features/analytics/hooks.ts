import { keepPreviousData, useQuery } from "@tanstack/react-query"

import { useTokenPresence } from "@/shared/hooks/useTokenPresence"
import type { ListFilters } from "@/shared/types/api"

import { getAnalyticsRequest } from "./api"

export const analyticsQueryKey = (filters: ListFilters = {}) => ["analytics", filters] as const

export function useAnalytics(filters: ListFilters = {}) {
  const hasToken = useTokenPresence()
  return useQuery({
    queryKey: analyticsQueryKey(filters),
    queryFn: () => getAnalyticsRequest(filters),
    enabled: hasToken,
    staleTime: Infinity,
    gcTime: 30 * 60_000,
    placeholderData: keepPreviousData
  })
}
