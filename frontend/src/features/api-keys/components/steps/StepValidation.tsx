import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

import type { ApiKeyErrorVariant } from "@/shared/lib/api-key-errors"
import { cn } from "@/shared/lib/cn"
import type { ApiKeyValidationResult } from "@/shared/types/api"
import { Btn } from "@/shared/ui/Btn"
import { btnClass } from "@/shared/ui/btn-class"
import { Ico } from "@/shared/ui/Ico"
import { Pill } from "@/shared/ui/Pill"
import { Spinner } from "@/shared/ui/Spinner"

type ValidationState =
  | { kind: "pending" }
  | { kind: "success"; result: ApiKeyValidationResult }
  | { kind: "error"; variant: ApiKeyErrorVariant; detail: string | null; code: string | null }

interface StepValidationProps {
  state: ValidationState
  onEditKey: () => void
  onClose: () => void
  onDone: () => void
}

const CHECKS = ["Verifying API key & secret", "Confirming read-only access", "Matching your markets"] as const

const STEP_MS = 450

function failedRowForCode(code: string | null): number {
  switch (code) {
    case "InvalidCredentialsError":
    case "DuplicateKeyError":
    case "IpNotWhitelistedError":
    case "RateLimitError":
    case "ExchangeUnavailableError":
      return 0
    case "KeyNotReadOnlyError":
    case "PlanLimitError":
      return 1
    case "KeyAccessRestrictedError":
      return 2
    default:
      return 0
  }
}

type RowState = "idle" | "running" | "done" | "fail"

export function StepValidation({ state, onEditKey, onClose, onDone }: StepValidationProps) {
  const failedRow = state.kind === "error" ? failedRowForCode(state.code) : -1

  const [cursor, setCursor] = useState(0)

  useEffect(() => {
    if (state.kind === "pending") {
      setCursor(0)
      return
    }
    const target = state.kind === "success" ? CHECKS.length : failedRow + 1
    setCursor(0)
    let i = 0
    const timer = window.setInterval(() => {
      i += 1
      setCursor(i)
      if (i >= target) window.clearInterval(timer)
    }, STEP_MS)
    return () => window.clearInterval(timer)
  }, [state.kind, failedRow])

  const rowState = (i: number): RowState => {
    if (state.kind === "pending") return i === 0 ? "running" : "idle"
    if (state.kind === "error") {
      if (i > failedRow) return "idle"
      if (i < cursor) return i === failedRow ? "fail" : "done"
      return i === cursor ? "running" : "idle"
    }
    if (i < cursor) return "done"
    return i === cursor ? "running" : "idle"
  }

  const showSuccess = state.kind === "success" && cursor >= CHECKS.length
  const showError = state.kind === "error" && cursor > failedRow

  return (
    <div className="flex flex-col gap-5 min-h-65">
      <ol className="flex flex-col gap-2">
        {CHECKS.map((label, i) => (
          <CheckRow key={label} label={label} state={rowState(i)} />
        ))}
      </ol>

      {showSuccess && state.kind === "success" && <SuccessSummary result={state.result} onDone={onDone} />}
      {showError && state.kind === "error" && (
        <ErrorSummary variant={state.variant} detail={state.detail} onEditKey={onEditKey} onClose={onClose} />
      )}
    </div>
  )
}

function SuccessSummary({ result, onDone }: { result: ApiKeyValidationResult; onDone: () => void }) {
  return (
    <>
      <div className="flex flex-col gap-3 px-4 py-3.5 bg-bg-2 border border-line rounded-lg">
        <div className="flex items-center gap-2">
          <span className="size-7 rounded-full bg-profit-bg text-profit inline-flex items-center justify-center shrink-0">
            <Ico.Check width={16} height={16} strokeWidth={2.5} />
          </span>
          <span className="text-[14px] font-semibold text-fg-0">{result.replaced ? "Broken key replaced" : "Key connected"}</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {result.capabilities.length === 0
            ? <span className="text-[12px] text-fg-3">no markets detected</span>
            : result.capabilities.map(c => <Pill key={c} tone="profit" dot>{c}</Pill>)
          }
        </div>
        <p className="text-[12.5px] text-fg-1 m-0">
          {result.replaced
            ? "We re-linked your previous broken key's history to this one — sync resumes shortly"
            : "Your trades will be added shortly — you can close this window"}
        </p>
      </div>

      <footer className="flex items-center justify-end pt-4 border-t border-line">
        <Btn kind="primary" size="md" onClick={onDone}>Done</Btn>
      </footer>
    </>
  )
}

function ErrorSummary({
  variant, detail, onEditKey, onClose
}: { variant: ApiKeyErrorVariant; detail: string | null; onEditKey: () => void; onClose: () => void }) {
  return (
    <>
      <div className="flex flex-col gap-1.5 px-3.5 py-3 bg-loss-bg/40 border border-loss-bg rounded-lg">
        <div className="flex items-center gap-2">
          <Ico.Warn width={15} height={15} className="text-loss shrink-0" strokeWidth={2} />
          <span className="text-[13.5px] font-semibold text-fg-0">{variant.title}</span>
        </div>
        <p className="text-[12.5px] text-fg-1 leading-relaxed m-0">{variant.hint}</p>
        {detail && <p className="text-[11.5px] text-fg-2 leading-relaxed m-0">{detail}</p>}
      </div>

      <footer className="flex items-center justify-between pt-4 border-t border-line gap-3">
        <Btn kind="ghost" size="md" onClick={onClose}>Close</Btn>
        <div className="flex items-center gap-2">
          {variant.goBackTo === "plan" && (
            <Link to="/dashboard/settings" onClick={onClose} className={btnClass("outline", "md")}>
              View plans
            </Link>
          )}
          {variant.recoverable && variant.goBackTo === "credentials" && (
            <Btn kind="primary" size="md" onClick={onEditKey}>Edit key</Btn>
          )}
        </div>
      </footer>
    </>
  )
}

function CheckRow({ label, state }: { label: string; state: RowState }) {
  return (
    <li className="flex items-center gap-3 px-3.5 py-2.5 bg-bg-2 border border-line rounded-lg">
      <StateIcon state={state} />
      <span
        className={cn(
          "text-[13px]",
          state === "idle" ? "text-fg-3" : state === "running" ? "text-fg-1" : state === "done" ? "text-profit" : "text-loss"
        )}
      >
        {label}
      </span>
    </li>
  )
}

function StateIcon({ state }: { state: RowState }) {
  if (state === "running") {
    return (
      <span className="size-4 inline-flex items-center justify-center shrink-0">
        <Spinner size={12} tone="muted" />
      </span>
    )
  }
  if (state === "done") {
    return <Ico.Check width={16} height={16} className="text-profit shrink-0" strokeWidth={2.5} />
  }
  if (state === "fail") {
    return <Ico.X width={16} height={16} className="text-loss shrink-0" strokeWidth={2.5} />
  }
  return <span className="size-1.5 rounded-full bg-fg-3 shrink-0" aria-hidden />
}
