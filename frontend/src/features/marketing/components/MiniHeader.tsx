import { Link } from "react-router-dom"

import { useAuth } from "@/shared/hooks/useAuth"
import { btnClass } from "@/shared/ui/btn-class"
import { Ico } from "@/shared/ui/Ico"
import { Logo } from "@/shared/ui/Logo"
import { ThemeToggle } from "@/shared/ui/ThemeToggle"

export function MiniHeader() {
  const authed = useAuth().status === "authed"
  return (
    <header className="flex items-center justify-between px-4 sm:px-10 lg:px-14 py-4 sm:py-5">
      <Link to="/" aria-label="Tradeline home" className="rounded-md shrink-0">
        <Logo size={24} />
      </Link>
      <div className="flex items-center gap-2 sm:gap-2.5">
        <ThemeToggle size="sm" />
        {authed ? (
          <Link to="/dashboard" className={btnClass("primary", "sm")}>
            Open dashboard
            <Ico.Arrow width={14} height={14} />
          </Link>
        ) : (
          <Link to="/auth?mode=login" className={btnClass("ghost", "sm")}>
            Log in
          </Link>
        )}
      </div>
    </header>
  )
}
