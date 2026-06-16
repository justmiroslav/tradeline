export const PRO_MONTHLY_CENTS = 899
export const PRO_YEARLY_CENTS = 8999
export const PRO_YEARLY_EFFECTIVE_MONTHLY_CENTS = Math.round(PRO_YEARLY_CENTS / 12)
export const PRO_YEARLY_SAVINGS_PCT = Math.round((1 - PRO_YEARLY_EFFECTIVE_MONTHLY_CENTS / PRO_MONTHLY_CENTS) * 100)

export interface PlanFeature {
  label: string
}

export const BASIC_FEATURES: PlanFeature[] = [
  { label: "4 exchange connections" },
  { label: "3 months of trade history" },
  { label: "Pro-grade analytics" },
  { label: "Daily P&L calendar" },
  { label: "CSV export" },
  { label: "Instant trade sync" },
  { label: "Weekly AI insights" }
]

export const PRO_FEATURES: PlanFeature[] = [
  { label: "Unlimited exchange connections" },
  { label: "Daily AI insights" },
  { label: "Priority data refresh" },
  { label: "Early access to advanced visualisations" }
]
