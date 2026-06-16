import { useState } from "react"

import { useInvoices, useSubscription } from "../hooks"
import { InvoiceHistory } from "./InvoiceHistory"
import { PlanSummary } from "./PlanSummary"
import { SubscriptionDialog } from "./SubscriptionDialog"

export function BillingPanel() {
  const [subscribeOpen, setSubscribeOpen] = useState(false)
  const { data: sub } = useSubscription()
  const hasBilling = !!sub?.has_billing
  const { data: invoices } = useInvoices(hasBilling)

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_1fr] gap-5 items-stretch">
        <div className="flex flex-col rounded-xl border border-line bg-bg-1 p-5 shadow-card">
          <div className="text-[11.5px] uppercase tracking-[0.08em] text-fg-2 mb-3">Plan</div>
          <PlanSummary subscription={sub} onUpgrade={() => setSubscribeOpen(true)} />
        </div>
        {hasBilling && (
          <div className="flex-1 min-h-40 flex flex-col rounded-xl border border-line bg-bg-1 p-5 shadow-card">
            <div className="text-[11.5px] uppercase tracking-[0.08em] text-fg-2 mb-3">Invoices</div>
            <InvoiceHistory invoices={invoices ?? []} />
          </div>
        )}
      </div>

      <SubscriptionDialog open={subscribeOpen} onOpenChange={setSubscribeOpen} />
    </>
  )
}
