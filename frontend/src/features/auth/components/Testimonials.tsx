import { StarRating, usePublicReviews } from "@/features/reviews"
import type { ReviewOut } from "@/shared/types/api"
import { Ico } from "@/shared/ui/Ico"

const VALUE_PROPS = [
  "Four exchanges, free",
  "Pro is $8.99 a month",
  "Per-setup and per-symbol stats with an honest AI read on your real edge"
]

export function Testimonials() {
  const reviews = usePublicReviews().data ?? []
  const shown = reviews.slice(0, 2)

  return (
    <div className="relative overflow-hidden border-t border-line lg:border-t-0 lg:border-l bg-bg-1 p-6 sm:p-10 lg:p-12 flex flex-col justify-center gap-7">
      <div
        className="absolute pointer-events-none"
        style={{
          top: -120,
          right: -80,
          width: 380,
          height: 380,
          background: "radial-gradient(closest-side, var(--accent-glow), transparent 70%)"
        }}
        aria-hidden
      />

      <div className="relative flex flex-col gap-5">
        <div>
          <span className="mono text-[11.5px] uppercase tracking-[0.12em] text-fg-2">Why traders switch</span>
          <h2
            className="text-[clamp(22px,3vw,26px)] font-semibold m-0 mt-2 text-fg-0 leading-[1.15]"
            style={{ letterSpacing: "-0.025em", textWrap: "balance" }}
          >
            A serious journal that stays affordable
          </h2>
        </div>
        <div className="grid grid-cols-2 gap-2.5">
          <ValueProp text={VALUE_PROPS[0]} />
          <ValueProp text={VALUE_PROPS[1]} />
          <ValueProp text={VALUE_PROPS[2]} className="col-span-2" />
        </div>
      </div>

      {shown.length > 0 && (
        <div className="relative flex flex-col gap-3">
          <span className="mono text-[11.5px] uppercase tracking-[0.12em] text-fg-2">From traders using it</span>
          {shown.map(r => <ReviewCard key={r.id} review={r} />)}
        </div>
      )}
    </div>
  )
}

function ValueProp({ text, className }: { text: string; className?: string }) {
  return (
    <div className={`flex items-start gap-2.5 px-4 py-3.5 border border-line rounded-[14px] bg-bg-2 ${className ?? ""}`}>
      <span className="shrink-0 mt-0.5 text-accent"><Ico.Check width={15} height={15} /></span>
      <span className="text-[12.5px] leading-[1.45] text-fg-0">{text}</span>
    </div>
  )
}

function ReviewCard({ review }: { review: ReviewOut }) {
  return (
    <div className="px-5 py-4 border border-line rounded-[14px] bg-bg-2">
      <StarRating value={review.rating} size={14} />
      <div
        className="text-[13.5px] leading-[1.55] text-fg-0 my-3"
        style={{ letterSpacing: "-0.005em", textWrap: "balance" }}
      >
        &ldquo;{review.body}&rdquo;
      </div>
      <div className="flex items-center gap-3">
        <div className="size-7.5 rounded-full bg-accent-glow text-accent inline-flex items-center justify-center text-[11.5px] font-semibold shrink-0">
          {review.name[0]}
        </div>
        <div className="text-[12.5px] font-medium text-fg-0 truncate">{review.name}</div>
      </div>
    </div>
  )
}
