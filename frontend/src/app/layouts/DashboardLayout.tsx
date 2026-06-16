import { type CSSProperties, Suspense, useState } from "react"
import { Outlet } from "react-router-dom"

import { DashboardNavContext } from "@/app/shell/dashboard-nav"
import { Sidebar } from "@/app/shell/Sidebar"
import { FiltersProvider } from "@/features/filters"
import { useLiveSync } from "@/shared/hooks/useLiveSync"
import { useViewportScale } from "@/shared/hooks/useViewportScale"

export function DashboardLayout() {
  const [open, setOpen] = useState(false)
  const scale = useViewportScale()
  useLiveSync()

  return (
    <FiltersProvider>
      <DashboardNavContext.Provider value={{ open, setOpen }}>
        <div
          className="tl-scale-host overflow-hidden bg-bg-0 text-fg-0 font-sans lg:grid lg:grid-cols-[232px_minmax(0,1fr)]"
          style={{ "--tl-zoom": scale } as CSSProperties}
        >
          <Sidebar />
          <main className="min-w-0 h-full overflow-hidden flex flex-col">
            <Suspense fallback={<div className="flex-1 flex items-center justify-center"><span className="size-2 rounded-full bg-accent animate-tl-pulse" aria-hidden /></div>}>
              <Outlet />
            </Suspense>
          </main>
        </div>
      </DashboardNavContext.Provider>
    </FiltersProvider>
  )
}
