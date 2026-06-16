import { Link } from "react-router-dom"

import { useTokenPresence } from "@/shared/hooks/useTokenPresence"
import { btnClass } from "@/shared/ui/btn-class"

export default function NotFound() {
  const authed = useTokenPresence()
  const home = authed ? "/dashboard" : "/"

  return (
    <div className="min-h-dvh bg-bg-0 text-fg-0 font-sans flex flex-col items-center justify-center gap-5 px-6">
      <div className="mono text-[11.5px] uppercase tracking-[0.12em] text-fg-2">404</div>
      <h1
        className="text-[clamp(30px,6vw,42px)] font-semibold m-0 text-center"
        style={{ letterSpacing: "-0.025em" }}
      >
        This page doesn't exist
      </h1>
      <p className="text-fg-1 text-[14px] text-center max-w-105">
        You've hit a URL that isn't part of Tradeline — check the address or head back
      </p>
      <Link to={home} className={btnClass("primary", "md")}>
        Take me home
      </Link>
    </div>
  )
}
