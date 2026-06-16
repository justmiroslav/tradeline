import { useMutation, useQuery } from "@tanstack/react-query"

import { getInvoicesRequest, getSubscriptionRequest, openPortalRequest, startCheckoutRequest } from "./api"

export const subscriptionQueryKey = ["billing", "subscription"] as const
export const invoicesQueryKey = ["billing", "invoices"] as const

export function useSubscription() {
  return useQuery({
    queryKey: subscriptionQueryKey,
    queryFn: getSubscriptionRequest,
    staleTime: 30_000,
    refetchOnWindowFocus: true
  })
}

export function useInvoices(enabled: boolean) {
  return useQuery({
    queryKey: invoicesQueryKey,
    queryFn: getInvoicesRequest,
    enabled,
    staleTime: 60_000,
    refetchOnWindowFocus: true
  })
}

export function useStartCheckout() {
  return useMutation({
    mutationFn: startCheckoutRequest,
    onSuccess: res => window.location.assign(res.url)
  })
}

export function useOpenPortal() {
  return useMutation({
    mutationFn: openPortalRequest,
    onSuccess: res => window.location.assign(res.url)
  })
}
