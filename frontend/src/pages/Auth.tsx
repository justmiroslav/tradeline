import * as Tabs from "@radix-ui/react-tabs"
import { type ReactNode, useEffect, useState } from "react"
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom"

import { DASHBOARD_HOME, EmailVerificationPanel, LoginForm, RegisterForm, Testimonials } from "@/features/auth"
import { useAuth } from "@/shared/hooks/useAuth"
import { cn } from "@/shared/lib/cn"
import { env } from "@/shared/lib/env"
import { btnClass } from "@/shared/ui/btn-class"
import { GoogleBtn } from "@/shared/ui/GoogleBtn"
import { Ico } from "@/shared/ui/Ico"
import { Logo } from "@/shared/ui/Logo"
import { ThemeToggle } from "@/shared/ui/ThemeToggle"

type Mode = "login" | "register"

export default function Auth() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const initialMode: Mode = params.get("mode") === "register" ? "register" : "login"
  const [mode, setMode] = useState<Mode>(initialMode)
  const [proIntent] = useState(() => params.get("plan") === "pro")
  const [pendingEmail, setPendingEmail] = useState<string | null>(null)
  const [fading, setFading] = useState(false)
  const { status } = useAuth()

  const registerDestination = proIntent ? "/checkout" : DASHBOARD_HOME

  const swapTo = (email: string | null) => {
    setFading(true)
    setTimeout(() => {
      setPendingEmail(email)
      setFading(false)
    }, 220)
  }

  const leaveTo = (destination: string) => {
    setFading(true)
    setTimeout(() => navigate(destination, { replace: true }), 260)
  }

  useEffect(() => {
    if (params.get("mode") !== mode || params.has("plan")) {
      const next = new URLSearchParams()
      next.set("mode", mode)
      setParams(next, { replace: true })
    }
  }, [mode, params, setParams])

  if (status === "authed" && !pendingEmail) return <Navigate to={DASHBOARD_HOME} replace />

  return (
    <div className="min-h-dvh grid grid-cols-1 lg:grid-cols-2 font-sans">
      <div className="relative bg-bg-0 lg:h-dvh overflow-y-auto">
        <div className="absolute top-5 left-5 sm:top-6 sm:left-7 z-10">
          <Link to="/" className={btnClass("ghost", "sm")} aria-label="Back to home">
            <Ico.ArrowL width={14} height={14} />
            Back to home
          </Link>
        </div>
        <div className="absolute top-5 right-5 sm:top-6 sm:right-7 z-10">
          <ThemeToggle size="sm" />
        </div>

        {pendingEmail ? (
          <div
            key="verify"
            className={cn(
              "w-full max-w-[420px] mx-auto pt-20 pb-12 px-6 flex flex-col gap-6 animate-tl-tab-fade",
              "transition-opacity duration-200",
              fading && "opacity-0"
            )}
          >
            <Logo size={24} />
            <EmailVerificationPanel
              email={pendingEmail}
              onVerified={() => leaveTo(registerDestination)}
              onBack={() => swapTo(null)}
            />
          </div>
        ) : (
          <Tabs.Root key="tabs" value={mode} onValueChange={v => setMode(v as Mode)}>
            <div className={cn(
              "w-full max-w-[420px] mx-auto pt-20 pb-12 px-6 flex flex-col gap-5 animate-tl-tab-fade",
              "transition-opacity duration-200",
              fading && "opacity-0"
            )}>
              <Logo size={24} />

              <div className="relative h-14.5">
                <AuthHeading title="Welcome back" subtitle="Log in to your dashboard" visible={mode === "login"} />
                <AuthHeading title="Create your Tradeline" subtitle="Three minutes to a live dashboard" visible={mode === "register"} />
              </div>

              <Tabs.List
                className="relative grid grid-cols-2 p-1 bg-bg-2 rounded-[10px] border border-line"
                aria-label="Authentication mode"
              >
                <span
                  aria-hidden
                  className="absolute top-1 bottom-1 left-1 w-[calc(50%-4px)] rounded-md shadow-card pointer-events-none"
                  style={{
                    background: "var(--accent)",
                    transform: `translateX(${mode === "register" ? "100%" : "0"})`,
                    transition: "transform 360ms cubic-bezier(0.16, 1, 0.3, 1)"
                  }}
                />
                <AuthTab value="login" active={mode === "login"}>Log in</AuthTab>
                <AuthTab value="register" active={mode === "register"}>Create account</AuthTab>
              </Tabs.List>

              {env.googleClientId && (
                <>
                  <GoogleBtn text={mode === "login" ? "signin_with" : "signup_with"} />
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-px bg-line" />
                    <span className="text-[11.5px] uppercase tracking-[0.08em] text-fg-2">or with email</span>
                    <div className="flex-1 h-px bg-line" />
                  </div>
                </>
              )}

              <Tabs.Content value="login" className="outline-none animate-tl-tab-fade">
                <LoginForm />
              </Tabs.Content>
              <Tabs.Content value="register" className="outline-none animate-tl-tab-fade">
                <RegisterForm onRegistered={swapTo} />
              </Tabs.Content>
            </div>
          </Tabs.Root>
        )}
      </div>

      <Testimonials />
    </div>
  )
}

interface AuthHeadingProps {
  title: string
  subtitle: string
  visible: boolean
}

function AuthHeading({ title, subtitle, visible }: AuthHeadingProps) {
  return (
    <div
      aria-hidden={!visible}
      className="absolute inset-0"
      style={{
        opacity: visible ? 1 : 0,
        pointerEvents: visible ? "auto" : "none",
        transition: "opacity 280ms cubic-bezier(0.16, 1, 0.3, 1)"
      }}
    >
      <h1 className="text-[26px] font-semibold m-0 mb-1.5 text-fg-0" style={{ letterSpacing: "-0.025em" }}>
        {title}
      </h1>
      <p className="text-[13.5px] text-fg-1 m-0">{subtitle}</p>
    </div>
  )
}

function AuthTab({ value, active, children }: { value: string; active: boolean; children: ReactNode }) {
  return (
    <Tabs.Trigger
      value={value}
      className={cn("relative z-10 py-2.5 text-[13px] rounded-md cursor-pointer", active ? "font-semibold" : "hover:text-fg-1")}
      style={{
        color: active ? "var(--accent-fg)" : "var(--fg-2)",
        transition: "color 360ms cubic-bezier(0.16, 1, 0.3, 1)"
      }}
    >
      {children}
    </Tabs.Trigger>
  )
}
