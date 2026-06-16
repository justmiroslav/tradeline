import { type ReactElement, useLayoutEffect, useRef, useState } from "react"
import { ResponsiveContainer } from "recharts"

interface ChartFrameProps {
  height: number
  empty?: boolean
  emptyHint?: string
  scrollWidth?: number
  children: ReactElement
}

export function ChartFrame({ height, empty, emptyHint = "No data for this range", scrollWidth, children }: ChartFrameProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    if (el.clientWidth > 0) {
      setReady(true)
      return
    }
    const obs = new ResizeObserver(entries => {
      if (entries[0].contentRect.width > 0) {
        setReady(true)
        obs.disconnect()
      }
    })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  const chart = ready ? <ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer> : null

  return (
    <div ref={ref} style={{ height }} className={scrollWidth ? "w-full overflow-x-auto tl-scroll-thin" : "w-full"}>
      {empty ? (
        <div className="size-full flex items-center justify-center text-[12.5px] text-fg-3">{emptyHint}</div>
      ) : scrollWidth ? (
        <div style={{ width: scrollWidth, height: "100%" }}>{chart}</div>
      ) : (
        chart
      )}
    </div>
  )
}
