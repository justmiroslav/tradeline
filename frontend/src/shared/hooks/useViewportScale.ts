import { useLayoutEffect, useState } from "react"

const DESIGN_WIDTH = 1920
const DESIGN_HEIGHT = 1080
const MAX_SCALE = 3

export function useViewportScale(): number {
  const [scale, setScale] = useState(1)

  useLayoutEffect(() => {
    const compute = () => {
      const el = document.documentElement
      const fit = Math.min(el.clientWidth / DESIGN_WIDTH, el.clientHeight / DESIGN_HEIGHT)
      const clamped = Math.min(MAX_SCALE, Math.max(1, fit))
      setScale(Math.round(clamped * 1000) / 1000)
    }
    compute()
    window.addEventListener("resize", compute)
    return () => window.removeEventListener("resize", compute)
  }, [])

  return scale
}
