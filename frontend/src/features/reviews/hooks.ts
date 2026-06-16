import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useTokenPresence } from "@/shared/hooks/useTokenPresence"

import { getMyReviewRequest, getReviewsRequest, submitReviewRequest } from "./api"

export const publicReviewsKey = ["reviews", "public"] as const
export const myReviewKey = ["reviews", "me"] as const

export function usePublicReviews() {
  return useQuery({
    queryKey: publicReviewsKey,
    queryFn: getReviewsRequest,
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: true
  })
}

export function useMyReview() {
  const hasToken = useTokenPresence()
  return useQuery({
    queryKey: myReviewKey,
    queryFn: getMyReviewRequest,
    enabled: hasToken,
    staleTime: 20_000,
    refetchOnWindowFocus: true,
    refetchInterval: query => (query.state.data?.status === "pending" ? 15_000 : false)
  })
}

export function useSubmitReview() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ rating, body }: { rating: number; body: string }) => submitReviewRequest(rating, body),
    onSuccess: data => queryClient.setQueryData(myReviewKey, data)
  })
}
