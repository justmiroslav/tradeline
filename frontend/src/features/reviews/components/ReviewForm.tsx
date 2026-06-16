import { useEffect, useRef, useState } from "react"

import { cn } from "@/shared/lib/cn"
import { Btn } from "@/shared/ui/Btn"
import { Pill, type PillTone } from "@/shared/ui/Pill"

import { useMyReview, useSubmitReview } from "../hooks"
import { StarRating } from "./StarRating"

const STATUS_TONE: Record<string, PillTone> = { approved: "profit", pending: "warn", rejected: "neutral" }

export function ReviewForm({ className }: { className?: string }) {
  const { data: existing } = useMyReview()
  const submit = useSubmitReview()
  const [rating, setRating] = useState(0)
  const [body, setBody] = useState("")
  const [flash, setFlash] = useState(false)
  const hydrated = useRef(false)

  useEffect(() => {
    if (existing && !hydrated.current) {
      hydrated.current = true
      setRating(existing.rating)
      setBody(existing.body)
    }
  }, [existing])

  useEffect(() => {
    if (!flash) return
    const t = setTimeout(() => setFlash(false), 2500)
    return () => clearTimeout(t)
  }, [flash])

  const trimmed = body.trim()
  const valid = rating >= 1 && trimmed.length >= 10 && body.length <= 500
  const changed = !existing || rating !== existing.rating || trimmed !== existing.body
  const canSubmit = valid && changed && !submit.isPending

  const onSubmit = () => submit.mutate({ rating, body: trimmed }, { onSuccess: () => setFlash(true) })

  return (
    <section className={cn("rounded-xl border border-line bg-bg-1 p-5 shadow-card", className)}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11.5px] uppercase tracking-[0.08em] text-fg-2">Share your experience</span>
        {existing && <Pill tone={STATUS_TONE[existing.status] ?? "neutral"} className="capitalize">{existing.status}</Pill>}
      </div>
      <div className="flex flex-col gap-3.5">
        <div className="flex items-center gap-3">
          <span className="text-[12.5px] text-fg-1">Your rating</span>
          <StarRating value={rating} onChange={setRating} size={22} />
        </div>
        <textarea
          value={body}
          onChange={e => setBody(e.target.value)}
          maxLength={500}
          rows={3}
          placeholder="What's working for you, what isn't? Approved reviews appear on our sign-in page"
          className="w-full resize-none rounded-lg bg-bg-2 border border-line px-3 py-2.5 text-[13px] text-fg-0 outline-none focus:border-accent transition-colors"
        />
        <div className="flex items-center justify-between gap-3 min-h-7">
          <span className="text-[11px] text-fg-3">{body.length}/500</span>
          <div className="flex items-center gap-3">
            <span
              className={cn("text-[11.5px] text-profit transition-opacity duration-500", flash ? "opacity-100" : "opacity-0")}
              aria-live="polite"
            >
              Saved, pending review
            </span>
            <Btn kind="primary" size="sm" disabled={!canSubmit} onClick={onSubmit}>
              {submit.isPending ? "Sending…" : existing ? "Update review" : "Submit review"}
            </Btn>
          </div>
        </div>
      </div>
    </section>
  )
}
