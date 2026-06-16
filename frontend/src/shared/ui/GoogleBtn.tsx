import { useEffect, useRef, useState } from "react"

import { useAuth } from "@/shared/hooks/useAuth"
import { env } from "@/shared/lib/env"

const GIS_SRC = "https://accounts.google.com/gsi/client?hl=en"

interface GsiId {
  initialize: (config: { client_id: string; callback: (resp: { credential: string }) => void }) => void
  renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void
}

declare global {
  interface Window {
    google?: { accounts: { id: GsiId } }
  }
}

function loadGis(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GIS_SRC}"]`)
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true })
      existing.addEventListener("error", () => reject(new Error("gis")), { once: true })
      return
    }
    const script = document.createElement("script")
    script.src = GIS_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error("gis"))
    document.head.appendChild(script)
  })
}

function GoogleMark() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" aria-hidden className="shrink-0">
      <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" />
      <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" />
      <path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" />
      <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" />
    </svg>
  )
}

interface GoogleBtnProps {
  text: "signin_with" | "signup_with"
}

export function GoogleBtn({ text }: GoogleBtnProps) {
  const { completeGoogleLogin } = useAuth()
  const overlayRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    const host = overlayRef.current
    if (!env.googleClientId || !host) return
    let cancelled = false

    loadGis()
      .then(() => {
        if (cancelled || !window.google) return
        window.google.accounts.id.initialize({
          client_id: env.googleClientId,
          callback: resp => {
            setError(false)
            completeGoogleLogin(resp.credential).catch(() => { if (!cancelled) setError(true) })
          }
        })
        host.replaceChildren()
        const width = Math.min(400, Math.max(240, Math.round(host.getBoundingClientRect().width) || 360))
        window.google.accounts.id.renderButton(host, {
          type: "standard",
          theme: "outline",
          size: "large",
          text,
          width
        })
      })
      .catch(() => {})

    return () => { cancelled = true }
  }, [completeGoogleLogin, text])

  if (!env.googleClientId) return null

  const label = text === "signup_with" ? "Sign up with Google" : "Continue with Google"

  return (
    <div className="flex flex-col gap-1.5">
      <div className="relative h-10 w-full">
        <div
          aria-hidden
          className="absolute inset-0 rounded-lg bg-bg-2 border border-line flex items-center justify-center gap-2.5 text-[14px] font-medium text-fg-0 select-none pointer-events-none"
        >
          <GoogleMark />
          {label}
        </div>
        <div ref={overlayRef} className="absolute inset-0 opacity-0 overflow-hidden flex justify-center" />
      </div>
      {error && <p className="text-[11.5px] text-loss m-0">Google sign-in failed — please try again</p>}
    </div>
  )
}
