import { useState } from "react"

import { PRO_MONTHLY_CENTS, PRO_YEARLY_EFFECTIVE_MONTHLY_CENTS, PRO_YEARLY_SAVINGS_PCT } from "@/features/plan"
import { formatPrice } from "@/shared/lib/format"
import { type BillingCycle, BillingCycleToggle } from "@/shared/ui/BillingCycleToggle"
import { Btn } from "@/shared/ui/Btn"
import { Ico } from "@/shared/ui/Ico"

import { useStartCheckout } from "../hooks"

export function SubscriptionForm() {
  const [cycle, setCycle] = useState<BillingCycle>("yearly")
  const checkout = useStartCheckout()

  const priceCents = cycle === "yearly" ? PRO_YEARLY_EFFECTIVE_MONTHLY_CENTS : PRO_MONTHLY_CENTS
  const billingNote = cycle === "yearly" ? "billed annually" : "billed monthly"

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center gap-3">
        <BillingCycleToggle value={cycle} onChange={setCycle} savingsPct={PRO_YEARLY_SAVINGS_PCT} size="sm" />
        <div className="text-center">
          <div className="flex items-baseline justify-center gap-1.5">
            <span className="mono tnum text-[34px] font-semibold text-fg-0 leading-none" style={{ letterSpacing: "-0.03em" }}>
              {formatPrice(priceCents)}
            </span>
            <span className="text-[12.5px] text-fg-2">/ mo</span>
          </div>
          <div className="text-[11.5px] text-fg-2 mt-1.5">{billingNote}</div>
        </div>
      </div>

      <div className="flex flex-col gap-2.5">
        <Btn
          kind="primary"
          full
          disabled={checkout.isPending}
          onClick={() => checkout.mutate(cycle)}
          leading={<Ico.Crown width={14} height={14} />}
        >
          {checkout.isPending ? "Redirecting…" : "Continue to checkout"}
        </Btn>
        {checkout.isError && (
          <p className="text-[11.5px] text-loss text-center m-0">Couldn't start checkout, please try again</p>
        )}
        <p className="text-[11.5px] text-fg-2 text-center m-0">
          Secure payment via Stripe, cancel anytime
        </p>
      </div>
    </div>
  )
}
