import { Segmented, type SegmentedOption } from "@/shared/ui/Segmented"

export type BillingCycle = "monthly" | "yearly"

interface BillingCycleToggleProps {
  value: BillingCycle
  onChange: (cycle: BillingCycle) => void
  savingsPct?: number
  size?: "sm" | "md"
  className?: string
}

export function BillingCycleToggle({ value, onChange, savingsPct = 17, size = "md", className }: BillingCycleToggleProps) {
  const options: SegmentedOption<BillingCycle>[] = [
    { value: "monthly", label: "Monthly" },
    {
      value: "yearly",
      label: (
        <span className="inline-flex items-center gap-1">
          Annually
          <span className="px-1 py-0.5 rounded-full bg-accent-glow text-accent text-[9px] font-semibold tracking-wide leading-none">
            −{savingsPct}%
          </span>
        </span>
      )
    }
  ]

  return (
    <Segmented value={value} onChange={onChange} options={options} ariaLabel="Billing cycle" size={size} className={className} />
  )
}
