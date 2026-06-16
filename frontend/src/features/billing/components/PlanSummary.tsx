import { BASIC_FEATURES, PRO_FEATURES } from "@/features/plan"
import { cn } from "@/shared/lib/cn"
import { formatDate } from "@/shared/lib/format"
import { Btn } from "@/shared/ui/Btn"
import { Ico } from "@/shared/ui/Ico"

import { useOpenPortal } from "../hooks"
import type { SubscriptionOut } from "../types"

interface PlanSummaryProps {
  subscription?: SubscriptionOut
  onUpgrade: () => void
}

export function PlanSummary({ subscription, onUpgrade }: PlanSummaryProps) {
  const portal = useOpenPortal()
  const isPro = subscription?.plan === "pro"
  const features = isPro ? PRO_FEATURES : BASIC_FEATURES
  const renewal = subscription?.current_period_end ? formatDate(subscription.current_period_end) : null

  const subtitle = isPro
    ? subscription?.cancel_at_period_end && renewal
      ? `Cancels on ${renewal}`
      : renewal
        ? `Renews on ${renewal}`
        : "Unlimited scale and priority — you're all set"
    : "Full analytics, calendar and CSV — all included"

  return (
    <div className="flex flex-col flex-1 gap-4">
      <div className="flex items-center gap-3">
        <span
          className={cn(
            "size-10 rounded-xl inline-flex items-center justify-center shrink-0",
            isPro ? "bg-accent-glow text-accent" : "bg-bg-2 text-fg-2"
          )}
        >
          {isPro ? <Ico.Crown width={20} height={20} /> : <Ico.Bolt width={20} height={20} />}
        </span>
        <div className="min-w-0">
          <div className="text-[14px] font-semibold text-fg-0">
            {isPro ? "Everything unlocked" : "You're on Basic"}
          </div>
          <div className="text-[12px] text-fg-2 mt-0.5">{subtitle}</div>
        </div>
      </div>

      <ul className={cn("list-none p-0 m-0 grid gap-x-5 gap-y-2.5", isPro ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2")}>
        {features.map(f => (
          <li key={f.label} className="flex gap-2.5 text-[13px] text-fg-1 items-start">
            <span className="shrink-0 mt-0.5 text-accent">
              <Ico.Check width={13} height={13} />
            </span>
            {f.label}
          </li>
        ))}
      </ul>

      <div className="mt-auto pt-2">
        {isPro ? (
          <Btn
            kind="secondary"
            full
            disabled={portal.isPending}
            onClick={() => portal.mutate()}
            trailing={<Ico.Arrow width={14} height={14} />}
          >
            {portal.isPending ? "Opening…" : "Manage billing"}
          </Btn>
        ) : (
          <Btn kind="primary" full onClick={onUpgrade} leading={<Ico.Crown width={14} height={14} />}>
            Upgrade to Pro
          </Btn>
        )}
        {portal.isError && (
          <p className="text-[11.5px] text-loss text-center mt-2 m-0">Couldn't open billing, please try again</p>
        )}
      </div>
    </div>
  )
}
