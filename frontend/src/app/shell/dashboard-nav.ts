import { createContext, useContext } from "react"

export interface DashboardNav {
  open: boolean
  setOpen: (open: boolean) => void
}

export const DashboardNavContext = createContext<DashboardNav | null>(null)

export function useDashboardNav(): DashboardNav {
  const ctx = useContext(DashboardNavContext)
  if (!ctx) throw new Error("useDashboardNav must be used inside DashboardLayout")
  return ctx
}
