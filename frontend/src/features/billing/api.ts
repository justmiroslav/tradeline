import { request } from "@/shared/lib/api"

import type { CheckoutOut, InvoiceOut, PortalOut, SubscriptionOut } from "./types"

export function getSubscriptionRequest(): Promise<SubscriptionOut> {
  return request<SubscriptionOut>("/billing/subscription")
}

export function getInvoicesRequest(): Promise<InvoiceOut[]> {
  return request<InvoiceOut[]>("/billing/invoices")
}

export function startCheckoutRequest(cycle: "monthly" | "yearly"): Promise<CheckoutOut> {
  return request<CheckoutOut>("/billing/checkout", { method: "POST", body: { cycle } })
}

export function openPortalRequest(): Promise<PortalOut> {
  return request<PortalOut>("/billing/portal", { method: "POST" })
}
