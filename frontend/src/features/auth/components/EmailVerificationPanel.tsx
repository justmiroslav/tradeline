import { useEffect, useState } from "react"

import { useAuth } from "@/shared/hooks/useAuth"
import { ApiError } from "@/shared/lib/api"
import { Ico } from "@/shared/ui/Ico"
import { Pill } from "@/shared/ui/Pill"
import { Spinner } from "@/shared/ui/Spinner"

import { useResendRegistrationCode } from "../hooks"
import { CodeInput } from "./CodeInput"

const RESEND_COOLDOWN_SECONDS = 60
const CODE_LENGTH = 6

interface EmailVerificationPanelProps {
  email: string
  onVerified: () => void
  onBack: () => void
}

export function EmailVerificationPanel({ email, onVerified, onBack }: EmailVerificationPanelProps) {
  const { completeRegistration } = useAuth()
  const resend = useResendRegistrationCode()
  const [code, setCode] = useState("")
  const [verifying, setVerifying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cooldown, setCooldown] = useState(RESEND_COOLDOWN_SECONDS)
  const [inputEpoch, setInputEpoch] = useState(0)
  const [verified, setVerified] = useState(false)

  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setInterval(() => setCooldown(c => c - 1), 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  const onCodeChange = (next: string) => {
    setCode(next)
    if (error) setError(null)
  }

  const onComplete = async (filled: string) => {
    setVerifying(true)
    setError(null)
    try {
      await completeRegistration(email, filled)
      setVerifying(false)
      setVerified(true)
      await new Promise(resolve => setTimeout(resolve, 1100))
      onVerified()
    } catch (e) {
      setVerifying(false)
      setCode("")
      setError(e instanceof ApiError ? e.message : "Verification failed — try again")
    }
  }

  const onResend = () => {
    setError(null)
    setCode("")
    setInputEpoch(n => n + 1)
    resend.mutate(email, {
      onSuccess: () => setCooldown(RESEND_COOLDOWN_SECONDS),
      onError: (e) => setError(e instanceof ApiError ? e.message : "Could not send the code — try again later")
    })
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col items-center text-center gap-3">
        <span className="size-12 rounded-2xl bg-accent-glow text-accent inline-flex items-center justify-center">
          <Ico.Check width={22} height={22} />
        </span>
        <div>
          <h1 className="text-[22px] font-semibold m-0 mb-1.5 text-fg-0" style={{ letterSpacing: "-0.025em" }}>
            Check your inbox
          </h1>
          <p className="text-[13px] text-fg-1 m-0 leading-relaxed">
            We sent a 6-digit code to <span className="text-fg-0 font-medium">{email}</span>
          </p>
          <p className="text-[12px] text-fg-2 m-0 mt-1">
            It is checked automatically once the last digit is in
          </p>
        </div>
      </div>

      <CodeInput
        key={inputEpoch}
        length={CODE_LENGTH}
        value={code}
        onChange={onCodeChange}
        onComplete={onComplete}
        disabled={verifying || verified}
        invalid={!!error}
      />

      <div className="min-h-7 flex items-center justify-center">
        {verifying && (
          <span className="inline-flex items-center gap-2 text-[12.5px] text-fg-1">
            <Spinner size={12} />
            Verifying…
          </span>
        )}
        {verified && (
          <span className="inline-flex items-center gap-2 text-[12.5px] text-profit animate-tl-fade">
            <Ico.Check width={14} height={14} />
            Verified — taking you in…
          </span>
        )}
        {error && !verifying && <Pill tone="loss">{error}</Pill>}
      </div>

      <div className="flex items-center justify-between text-[12.5px]">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1.5 text-fg-2 hover:text-fg-0 cursor-pointer transition-colors"
        >
          <Ico.ArrowL width={12} height={12} />
          Back to sign-up
        </button>
        <button
          type="button"
          onClick={onResend}
          disabled={cooldown > 0 || resend.isPending || verified}
          className={
            cooldown > 0 || resend.isPending || verified
              ? "text-fg-3 opacity-50 cursor-default transition-colors tnum"
              : "text-fg-0 font-medium hover:text-accent cursor-pointer transition-colors tnum"
          }
        >
          {cooldown > 0 ? `Resend code in ${cooldown}s` : resend.isPending ? "Sending…" : "Resend code"}
        </button>
      </div>
    </div>
  )
}
