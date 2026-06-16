import type { PlanTier } from "@/shared/types/api"

export interface SubscriptionOut {
  plan: PlanTier
  status: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
  has_billing: boolean
  billing_enabled: boolean
}

export interface InvoiceOut {
  id: string
  number: string | null
  created: string
  amount_paid: number
  currency: string
  status: string | null
  invoice_pdf: string | null
  hosted_invoice_url: string | null
}

export interface CheckoutOut {
  url: string
}

export interface PortalOut {
  url: string
}
