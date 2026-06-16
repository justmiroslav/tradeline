import { flushSync } from "react-dom"

export function withViewTransition(update: () => void): void {
  const reduce = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  if (!reduce && typeof document.startViewTransition === "function") {
    document.startViewTransition(() => flushSync(update))
  } else {
    update()
  }
}
