import { useQuery } from "@tanstack/react-query"

import { getServerInfoRequest } from "./api"

export const serverInfoQueryKey = ["server-info"] as const

export function useServerInfo() {
  return useQuery({
    queryKey: serverInfoQueryKey,
    queryFn: getServerInfoRequest,
    staleTime: 60 * 60_000,
    retry: 1
  })
}
