import { createContext, useContext } from "react"

import type { LoginIn, RegisterIn } from "@/shared/types/api"

export type AuthStatus = "loading" | "authed" | "guest"

export interface AuthContextValue {
  status: AuthStatus
  login: (body: LoginIn) => Promise<void>
  register: (body: RegisterIn) => Promise<void>
  completeRegistration: (email: string, code: string) => Promise<void>
  completeGoogleLogin: (credential: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>")
  return ctx
}
