import { cn } from "@/shared/lib/cn"
import { Ico } from "@/shared/ui/Ico"

export const STEP_LABELS = ["Exchange", "Connect", "Validate"] as const

interface StepperProps {
  current: 1 | 2 | 3
}

export function Stepper({ current }: StepperProps) {
  return (
    <ol className="flex items-center gap-2" aria-label="Progress">
      {STEP_LABELS.map((label, i) => {
        const n = (i + 1) as 1 | 2 | 3
        const state = n < current ? "done" : n === current ? "active" : "idle"
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              aria-current={state === "active" ? "step" : undefined}
              className={cn(
                "size-6 rounded-full inline-flex items-center justify-center text-[11px] font-semibold transition-colors duration-300",
                state === "done" && "bg-accent text-accent-fg",
                state === "active" && "bg-accent-glow text-accent border border-accent",
                state === "idle" && "bg-bg-2 text-fg-3 border border-line"
              )}
            >
              {state === "done" ? <Ico.Check width={12} height={12} /> : n}
            </span>
            <span
              className={cn(
                "text-[12px] font-medium hidden sm:inline-block transition-colors duration-300",
                state === "active" ? "text-fg-0" : "text-fg-2"
              )}
            >
              {label}
            </span>
            {n < 3 && (
              <span
                aria-hidden
                className={cn(
                  "w-6 h-px shrink-0 mx-1 rounded-full transition-colors duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]",
                  n < current ? "bg-accent" : "bg-line"
                )}
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}
