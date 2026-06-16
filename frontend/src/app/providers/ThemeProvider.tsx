import { type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react"

import { type Theme, ThemeContext, type ThemeContextValue } from "@/shared/hooks/useTheme"

const STORAGE_KEY = "tl.theme"

function readInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark"
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === "dark" || stored === "light") return stored
  } catch {
    return "dark"
  }
  const prefersLight = window.matchMedia?.("(prefers-color-scheme: light)").matches
  return prefersLight ? "light" : "dark"
}

interface ThemeProviderProps {
  children: ReactNode
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(readInitialTheme)
  const firstRun = useRef(true)

  useEffect(() => {
    const root = document.documentElement

    if (firstRun.current) {
      firstRun.current = false
      root.setAttribute("data-theme", theme)
      try { localStorage.setItem(STORAGE_KEY, theme) } catch {}
      return
    }

    try { localStorage.setItem(STORAGE_KEY, theme) } catch {}
    root.classList.add("theme-switching")
    void root.offsetWidth
    root.setAttribute("data-theme", theme)

    const timer = window.setTimeout(() => root.classList.remove("theme-switching"), 380)

    return () => {
      clearTimeout(timer)
      root.classList.remove("theme-switching")
    }
  }, [theme])

  const setTheme = useCallback((t: Theme) => setThemeState(t), [])
  const toggle = useCallback(() => setThemeState(t => t === "dark" ? "light" : "dark"), [])

  const value = useMemo<ThemeContextValue>(() => ({ theme, setTheme, toggle }), [theme, setTheme, toggle])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
