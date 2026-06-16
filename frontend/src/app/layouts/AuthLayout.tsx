import { Outlet } from "react-router-dom"

export function AuthLayout() {
  return (
    <div className="min-h-dvh bg-bg-0 text-fg-0 font-sans">
      <Outlet />
    </div>
  )
}
