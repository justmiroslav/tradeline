import { Link } from "react-router-dom"

import { useAuth } from "@/shared/hooks/useAuth"
import { btnClass } from "@/shared/ui/btn-class"
import { Ico } from "@/shared/ui/Ico"

export function Hero() {
  const authed = useAuth().status === "authed"
  return (
    <section className="relative overflow-hidden px-6 sm:px-10 lg:px-14 pt-14 pb-16 sm:pt-24 sm:pb-24">
      <div
        className="absolute pointer-events-none"
        style={{
          top: -200,
          right: -160,
          width: 720,
          height: 720,
          background: "radial-gradient(closest-side, var(--accent-glow), transparent 70%)"
        }}
        aria-hidden
      />
      <div className="relative">
        <h1
          className="inline-block max-w-full font-semibold m-0 text-fg-0"
          style={{ fontSize: "clamp(26px, 4.6vw, 62px)", lineHeight: 1.05, letterSpacing: "-0.04em" }}
        >
          <span className="tl-type-1 block text-fg-2">Every trade across every exchange,</span>
          <span className="tl-type-2 block text-left sm:text-right text-accent">one journal</span>
        </h1>
        <div className="tl-hero-rest">
          <p className="mt-6 sm:mt-7 max-w-lg text-[clamp(14px,1.5vw,17px)] leading-relaxed text-fg-1">
            Tradeline plugs into Binance, Bybit, OKX and Bitget, syncs your trades and turns them
            into the analytics your spreadsheet was hiding
          </p>
          <div className="mt-7 sm:mt-8 flex flex-wrap items-center gap-3">
            {authed ? (
              <Link to="/dashboard" className={btnClass("primary", "lg")}>
                Open dashboard
                <Ico.Arrow width={16} height={16} />
              </Link>
            ) : (
              <>
                <Link to="/auth?mode=register" className={btnClass("primary", "lg")}>
                  Start free
                  <Ico.Arrow width={16} height={16} />
                </Link>
                <Link to="/auth?mode=login" className={btnClass("outline", "lg")}>
                  Log in
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
