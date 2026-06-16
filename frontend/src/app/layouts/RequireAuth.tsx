import type { ReactNode } from "react"
import { Navigate } from "react-router-dom"

import { useAuth } from "@/shared/hooks/useAuth"
import { Spinner } from "@/shared/ui/Spinner"

interface RequireAuthProps {
  children: ReactNode
}

export function RequireAuth({ children }: RequireAuthProps) {
  const { status } = useAuth()

  if (status === "loading") {
    return (
      <div className="min-h-dvh bg-bg-0 text-fg-2 flex items-center justify-center text-sm">
        <Spinner size={12} tone="muted" />
        <span className="sr-only">Loading…</span>
      </div>
    )
  }

  if (status === "guest") {
    return <Navigate to="/auth?mode=login" replace />
  }

  return <>{children}</>
}
