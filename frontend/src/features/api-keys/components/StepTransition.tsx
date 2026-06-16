import { type ReactNode, useLayoutEffect, useRef, useState } from "react"

interface StepTransitionProps {
  step: number
  children: ReactNode
}

export function StepTransition({ step, children }: StepTransitionProps) {
  const innerRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState<number>()

  useLayoutEffect(() => {
    const el = innerRef.current
    if (!el) return
    const measure = () => setHeight(el.offsetHeight)
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  return (
    <div
      className="relative overflow-hidden motion-safe:transition-[height] motion-safe:duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]"
      style={{ height }}
    >
      <div ref={innerRef} className="px-2">
        <div key={step} className="motion-safe:animate-tl-tab-fade">
          {children}
        </div>
      </div>
    </div>
  )
}
