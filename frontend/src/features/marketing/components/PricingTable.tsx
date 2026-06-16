import type { ReactNode } from "react"
import { useState } from "react"
import { Link } from "react-router-dom"

import {
  BASIC_FEATURES,
  type PlanFeature,
  PRO_FEATURES,
  PRO_MONTHLY_CENTS,
  PRO_YEARLY_EFFECTIVE_MONTHLY_CENTS,
  PRO_YEARLY_SAVINGS_PCT} from "@/features/plan"
import { cn } from "@/shared/lib/cn"
import { formatPrice } from "@/shared/lib/format"
import { PLAN_LABEL } from "@/shared/lib/plan"
import { type BillingCycle, BillingCycleToggle } from "@/shared/ui/BillingCycleToggle"
import { Ico } from "@/shared/ui/Ico"

export function PricingTable() {
  const [cycle, setCycle] = useState<BillingCycle>("yearly")
  const proCents = cycle === "yearly" ? PRO_YEARLY_EFFECTIVE_MONTHLY_CENTS : PRO_MONTHLY_CENTS
  const proSub = cycle === "yearly" ? "billed annually" : "billed monthly"

  const toggle = (
    <BillingCycleToggle value={cycle} onChange={setCycle} savingsPct={PRO_YEARLY_SAVINGS_PCT} size="sm" />
  )

  const proFeatures: PlanFeature[] = [{ label: "Everything in Basic, plus:" }, ...PRO_FEATURES]

  return (
    <section className="px-6 sm:px-10 lg:px-14 py-16 sm:py-24 border-t border-line">
      <div className="mb-9 sm:mb-11 text-center">
        <span className="mono text-[11.5px] uppercase tracking-[0.12em] text-fg-2">
          Pricing
        </span>
        <h2
          className="text-[clamp(28px,4.4vw,44px)] font-semibold m-0 mt-2.5 text-fg-0"
          style={{ letterSpacing: "-0.03em" }}
        >
          Generous free tier, affordable Pro
        </h2>
        <p className="text-[14px] text-fg-2 mt-3 max-w-md mx-auto leading-relaxed">
          Almost everything is free — Pro unlocks unlimited scale and the next wave of AI-driven features
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 max-w-3xl mx-auto items-stretch">
        <PricingCard
          tone="free"
          label={PLAN_LABEL.free}
          tagline="Get started — no card needed"
          priceDisplay="$0"
          priceUnit="forever"
          subline={null}
          ctaLabel="Start free"
          ctaHref="/auth?mode=register"
          features={BASIC_FEATURES}
          toggle={toggle}
          toggleVisible={false}
        />
        <PricingCard
          tone="pro"
          recommended
          label={PLAN_LABEL.pro}
          tagline="For power traders"
          priceDisplay={formatPrice(proCents)}
          priceUnit="/ mo"
          subline={proSub}
          ctaLabel="Start with Pro"
          ctaHref="/auth?mode=register&plan=pro"
          features={proFeatures}
          toggle={toggle}
          toggleVisible
        />
      </div>
    </section>
  )
}

interface PricingCardProps {
  tone: "free" | "pro"
  recommended?: boolean
  label: string
  tagline: string
  priceDisplay: string
  priceUnit: string
  subline: string | null
  ctaLabel: string
  ctaHref: string
  features: PlanFeature[]
  toggle: ReactNode
  toggleVisible: boolean
}

function PricingCard({ tone, recommended, label, tagline, priceDisplay, priceUnit, subline, ctaLabel, ctaHref, features, toggle, toggleVisible }: PricingCardProps) {
  const isPro = tone === "pro"
  return (
    <div className="relative">
      {recommended && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10 px-2.5 py-1 bg-accent text-accent-fg text-[10.5px] font-semibold rounded-full uppercase tracking-[0.06em] inline-flex items-center gap-1 leading-none shadow-[0_4px_14px_-4px_var(--color-accent-glow)]">
          <Ico.Crown width={10} height={10} />
          Recommended
        </div>
      )}
      <div
        className={cn(
          "relative h-full rounded-2xl bg-bg-1 p-6 sm:p-6.5 pt-7 overflow-hidden transition-shadow duration-200 ease-[cubic-bezier(0.16,1,0.3,1)]",
          isPro
            ? "ring-1 ring-accent/40 shadow-[0_0_28px_-6px_var(--color-accent-glow)] hover:shadow-[0_0_36px_-4px_var(--color-accent-glow)]"
            : "border border-line hover:border-line-strong"
        )}
      >
        {isPro && <div className="absolute top-0 left-0 right-0 h-[3px] bg-accent" />}

        <div className="text-[18px] font-semibold text-fg-0 mb-1">{label}</div>
        <div className="text-[12.5px] text-fg-2 mb-5">{tagline}</div>

        <div className={cn("mb-5 flex justify-center", !toggleVisible && "invisible")} aria-hidden={!toggleVisible}>
          {toggle}
        </div>

        <div className="mb-5">
          <div className="flex items-baseline gap-1.5">
            <span
              className="mono tnum text-[42px] font-semibold text-fg-0 leading-none"
              style={{ letterSpacing: "-0.03em" }}
            >
              {priceDisplay}
            </span>
            <span className="text-[12.5px] text-fg-2">{priceUnit}</span>
          </div>
          <div className="text-[12px] text-fg-2 mt-1.5 min-h-[16px]">{subline ?? ""}</div>
        </div>

        <Link
          to={ctaHref}
          className={cn(
            "block w-full text-center px-4 py-2.5 rounded-lg text-[13.5px] font-semibold tracking-tight transition-[transform,opacity] duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] active:scale-[0.98]",
            isPro
              ? "bg-accent text-accent-fg shadow-[0_4px_14px_-4px_var(--color-accent-glow)] hover:opacity-90"
              : "bg-bg-2 text-fg-0 border border-line hover:bg-bg-3"
          )}
        >
          {ctaLabel}
        </Link>

        <hr className="my-5.5 border-0 h-px bg-line" />

        <ul className="list-none p-0 m-0 flex flex-col gap-2.5">
          {features.map(f => (
            <li key={f.label} className="flex gap-2.5 text-[13px] text-fg-1 items-start">
              <span className="shrink-0 mt-0.5 text-accent">
                <Ico.Check width={13} height={13} />
              </span>
              {f.label}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
