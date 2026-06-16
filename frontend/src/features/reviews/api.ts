import { request } from "@/shared/lib/api"
import type { MyReviewOut, ReviewOut } from "@/shared/types/api"

export function getReviewsRequest(): Promise<ReviewOut[]> {
  return request<ReviewOut[]>("/reviews/", { auth: false })
}

export function getMyReviewRequest(): Promise<MyReviewOut | null> {
  return request<MyReviewOut | null>("/reviews/me")
}

export function submitReviewRequest(rating: number, body: string): Promise<MyReviewOut> {
  return request<MyReviewOut>("/reviews/", { method: "POST", body: { rating, body } })
}
