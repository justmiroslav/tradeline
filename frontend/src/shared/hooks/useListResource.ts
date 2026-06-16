import { keepPreviousData, useQuery } from "@tanstack/react-query"

import { useTokenPresence } from "@/shared/hooks/useTokenPresence"

export function useListResource<T>(queryKey: readonly unknown[], queryFn: () => Promise<T>) {
  const hasToken = useTokenPresence()
  return useQuery({
    queryKey,
    queryFn,
    enabled: hasToken,
    staleTime: Infinity,
    gcTime: 30 * 60_000,
    placeholderData: keepPreviousData
  })
}
