import { Link } from "react-router-dom"

import { LandingFooter, MiniHeader } from "@/features/marketing"
import { cn } from "@/shared/lib/cn"
import { btnClass } from "@/shared/ui/btn-class"
import { Ico } from "@/shared/ui/Ico"

export default function Terms() {
  return (
    <div className="flex flex-col min-h-screen">
      <MiniHeader />
      <section className="px-6 sm:px-10 lg:px-14 py-20 sm:py-28 max-w-2xl mx-auto flex flex-col gap-5 flex-1">
        <span className="mono text-[11.5px] uppercase tracking-[0.12em] text-fg-2">Legal</span>
        <h1
          className="text-[clamp(28px,4vw,40px)] font-semibold m-0 text-fg-0"
          style={{ letterSpacing: "-0.03em" }}
        >
          Terms of Service
        </h1>
        <p className="text-[15px] text-fg-1 leading-relaxed m-0">
          Our full Terms of Service are being finalized and will be published here before launch
        </p>
        <p className="text-[14px] text-fg-2 leading-relaxed m-0">
          In short — Tradeline connects to your exchanges with read-only keys only: it never places trades or
          withdrawals, and your keys are stored encrypted. You stay in control and can disconnect any key at any time
        </p>
        <Link to="/" className={cn(btnClass("outline", "md"), "w-fit mt-2")}>
          <Ico.ArrowL width={14} height={14} />
          Back home
        </Link>
      </section>
      <LandingFooter />
    </div>
  )
}
