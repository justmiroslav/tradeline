import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { SubscriptionForm } from "@/features/billing"
import { cn } from "@/shared/lib/cn"
import { Logo } from "@/shared/ui/Logo"

export default function Checkout() {
  const navigate = useNavigate()
  const [leaving, setLeaving] = useState(false)
  const goDashboard = () => {
    setLeaving(true)
    setTimeout(() => navigate("/dashboard", { replace: true }), 280)
  }

  return (
    <div className="min-h-dvh bg-bg-0 text-fg-0 font-sans flex flex-col items-center justify-center px-6 py-10">
      <div className={cn("w-full max-w-[440px] flex flex-col gap-6 animate-tl-tab-fade transition-opacity duration-300", leaving && "opacity-0")}>
        <div className="flex flex-col items-center gap-3 text-center">
          <Logo size={26} />
          <div>
            <h1 className="text-[22px] font-semibold m-0 text-fg-0" style={{ letterSpacing: "-0.02em" }}>
              Start your Pro subscription
            </h1>
            <p className="text-[13.5px] text-fg-1 m-0 mt-1.5">
              One step left — set up billing to unlock Pro
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-line bg-bg-1 p-6 sm:p-7 shadow-card">
          <SubscriptionForm />
        </div>

        <button
          type="button"
          onClick={goDashboard}
          className="text-[12.5px] text-fg-2 hover:text-fg-0 transition-colors mx-auto cursor-pointer"
        >
          Maybe later — continue on Basic
        </button>
      </div>
    </div>
  )
}
