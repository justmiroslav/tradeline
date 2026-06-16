import { useQuery } from "@tanstack/react-query"

import { listPlansRequest } from "./api"

export const plansQueryKey = ["plans"] as const

export function usePlans() {
  return useQuery({
    queryKey: plansQueryKey,
    queryFn: listPlansRequest,
    staleTime: 5 * 60_000
  })
}
