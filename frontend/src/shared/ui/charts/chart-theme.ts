import { useEffect, useState } from "react"

export interface ChartColors {
  accent: string
  profit: string
  loss: string
  warn: string
  grid: string
  axis: string
  pieProfit: string[]
  pieLoss: string[]
}

function readColors(): ChartColors {
  const s = getComputedStyle(document.documentElement)
  const v = (token: string) => s.getPropertyValue(token).trim()
  return {
    accent: v("--accent"),
    profit: v("--profit"),
    loss: v("--loss"),
    warn: v("--warn"),
    grid: v("--line"),
    axis: v("--fg-3"),
    pieProfit: Array.from({ length: 9 }, (_, i) => v(`--pie-profit-${i + 1}`)),
    pieLoss: Array.from({ length: 9 }, (_, i) => v(`--pie-loss-${i + 1}`))
  }
}

export function useChartColors(): ChartColors {
  const [colors, setColors] = useState<ChartColors>(readColors)
  useEffect(() => {
    const observer = new MutationObserver(() => setColors(readColors()))
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] })
    return () => observer.disconnect()
  }, [])
  return colors
}

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches)
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    const onChange = () => setReduced(mq.matches)
    mq.addEventListener("change", onChange)
    return () => mq.removeEventListener("change", onChange)
  }, [])
  return reduced
}
