import { cn } from "@/shared/lib/cn"
import type { AiInsightBody } from "@/shared/types/api"
import { Btn } from "@/shared/ui/Btn"
import { Ico } from "@/shared/ui/Ico"
import { Spinner } from "@/shared/ui/Spinner"

import { useAiInsight, useAiInsightFeedback, useStreamingInsight } from "../hooks"

const EMPTY: AiInsightBody = { verdict: "breakeven", headline: "", edge: [], leaks: [], actions: [] }

function untilText(iso: string): string {
  const ms = new Date(iso).getTime() - Date.now()
  if (ms <= 0) return "moments"
  const totalMinutes = Math.floor(ms / 60_000)
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  if (days > 0) return `${days}d ${hours}h`
  if (hours > 0) return `${hours}h`
  return `${totalMinutes % 60}m`
}

const VERDICT_TONE: Record<AiInsightBody["verdict"], string> = {
  profitable: "text-profit",
  breakeven: "text-fg-0",
  unprofitable: "text-loss"
}

export function AiInsightCard({ className }: { className?: string }) {
  const query = useAiInsight()
  const generate = useStreamingInsight()
  const feedback = useAiInsightFeedback()

  const data = query.data
  const insight = data?.insight ?? null
  const canGenerate = data?.can_generate ?? false
  const nextAt = data?.next_available_at ?? null
  const verified = data?.verified ?? false
  const rating = data?.feedback ?? null
  const errMsg = generate.error

  const streaming = generate.streaming
  const shown = streaming ? generate.partial ?? EMPTY : insight

  const action = (kind: "secondary" | "ghost", label: string) =>
    canGenerate ? (
      <Btn kind={kind} size="sm" onClick={() => generate.start()} leading={<Ico.Bolt width={14} height={14} />}>{label}</Btn>
    ) : (
      <span className="inline-flex items-center gap-1.5 rounded-md border border-accent/20 bg-accent/15 px-2.5 py-1 text-[11.5px] font-medium text-accent/70">
        <Ico.Bolt width={12} height={12} />
        {nextAt ? `Next insight in ${untilText(nextAt)}` : "On cooldown"}
      </span>
    )

  return (
    <section className={cn("rounded-xl border border-line bg-bg-1 shadow-card flex flex-col overflow-hidden xl:relative xl:self-stretch", className)}>
      <div className="flex flex-col min-h-0 flex-1 p-4 sm:p-5 xl:absolute xl:inset-0">
        <div className="flex items-center gap-3 mb-3 min-h-7 shrink-0">
          <h2 className="text-[13px] font-semibold text-fg-0 m-0">AI insight</h2>
        </div>

        {query.isPending ? (
          <div className="flex flex-1 items-center gap-2.5 text-[12.5px] text-fg-2">
            <Spinner /> Loading…
          </div>
        ) : shown ? (
          <div className="flex flex-col gap-3 min-h-0 flex-1">
            <p className={cn("text-[13px] font-semibold leading-snug shrink-0", VERDICT_TONE[shown.verdict])}>
              {shown.headline || "Analyzing your trades…"}
            </p>
            <div className="flex flex-col gap-3 min-h-0 flex-1 overflow-y-auto [scrollbar-gutter:stable] pr-0.5">
              <Section label="Edge" items={shown.edge} dot="bg-profit" />
              <Section label="Leaks" items={shown.leaks} dot="bg-loss" />
              <Section label="Actions" items={shown.actions} dot="bg-accent" />
            </div>
            <div className="flex items-center justify-between gap-3 pt-0.5 shrink-0">
              {streaming ? (
                <span className="inline-flex items-center gap-2 text-[11.5px] text-fg-2">
                  <Spinner /> Generating…
                </span>
              ) : (
                <>
                  <div className="flex items-center gap-2.5 min-w-0">
                    {verified && (
                      <span
                        className="inline-flex items-center gap-1 rounded-md bg-profit-bg px-2 py-0.5 text-[10.5px] font-medium text-profit shrink-0"
                        title="Verdict matches your realized P&L and cites only symbols you traded"
                      >
                        <Ico.Check width={11} height={11} /> Grounded
                      </span>
                    )}
                    <FeedbackButtons value={rating} pending={feedback.isPending} onRate={h => feedback.mutate(h)} />
                  </div>
                  {action("ghost", "Regenerate")}
                </>
              )}
            </div>
            {errMsg && <p className="text-[11.5px] text-loss shrink-0 m-0">{errMsg}</p>}
          </div>
        ) : (
          <div className="flex flex-1 flex-wrap items-center content-center justify-between gap-x-4 gap-y-2.5">
            <p className="text-[12.5px] text-fg-2 max-w-md">{errMsg ?? "Get an expert AI read on your edge, leaks and the setups to lean into"}</p>
            {action("secondary", "Generate insight")}
          </div>
        )}
      </div>
    </section>
  )
}

function Thumb({ down }: { down?: boolean }) {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden style={down ? { transform: "rotate(180deg)" } : undefined}>
      <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
    </svg>
  )
}

function FeedbackButtons({ value, pending, onRate }: { value: boolean | null; pending: boolean; onRate: (helpful: boolean) => void }) {
  if (value !== null) {
    return <span className="text-[10.5px] text-fg-3">{value ? "Marked helpful" : "Thanks for the feedback"}</span>
  }
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="text-[10.5px] text-fg-3 mr-0.5">Useful?</span>
      <button
        type="button"
        disabled={pending}
        onClick={() => onRate(true)}
        aria-label="Helpful"
        className="size-6 inline-flex items-center justify-center rounded-md border border-line text-fg-2 hover:text-profit hover:border-profit/40 transition-colors cursor-pointer disabled:opacity-50"
      >
        <Thumb />
      </button>
      <button
        type="button"
        disabled={pending}
        onClick={() => onRate(false)}
        aria-label="Not helpful"
        className="size-6 inline-flex items-center justify-center rounded-md border border-line text-fg-2 hover:text-loss hover:border-loss/40 transition-colors cursor-pointer disabled:opacity-50"
      >
        <Thumb down />
      </button>
    </span>
  )
}

function Section({ label, items, dot }: { label: string; items: string[]; dot: string }) {
  if (items.length === 0) return null
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10.5px] uppercase tracking-[0.06em] text-fg-3">{label}</span>
      <ul className="flex flex-col gap-1">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2 text-[12.5px] text-fg-1 leading-relaxed">
            <span className={cn("mt-1.5 size-1.5 rounded-full shrink-0", dot)} aria-hidden />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
