import { useQueryClient } from "@tanstack/react-query"
import { type ReactNode, useCallback, useMemo } from "react"

import { googleLoginRequest, loginRequest, logoutRequest, meQueryKey, registerRequest, registerVerifyRequest, useMe } from "@/features/auth"
import { AuthContext, type AuthContextValue, type AuthStatus } from "@/shared/hooks/useAuth"
import { useTokenPresence } from "@/shared/hooks/useTokenPresence"
import { authStorage } from "@/shared/lib/auth-storage"
import type { LoginIn, RegisterIn, TokenOut } from "@/shared/types/api"

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const queryClient = useQueryClient()
  const hasToken = useTokenPresence()
  const me = useMe()

  const status: AuthStatus = !hasToken ? "guest" : me.data ? "authed" : "loading"

  const enterSession = useCallback(async (tok: TokenOut) => {
    authStorage.set(tok.access_token)
    await queryClient.refetchQueries({ queryKey: meQueryKey })
  }, [queryClient])

  const login = useCallback(async (body: LoginIn) => {
    await enterSession(await loginRequest(body))
  }, [enterSession])

  const register = useCallback(async (body: RegisterIn) => {
    await registerRequest(body)
  }, [])

  const completeRegistration = useCallback(async (email: string, code: string) => {
    await enterSession(await registerVerifyRequest(email, code))
  }, [enterSession])

  const completeGoogleLogin = useCallback(async (credential: string) => {
    await enterSession(await googleLoginRequest(credential))
  }, [enterSession])

  const logout = useCallback(async () => {
    try { await logoutRequest() } catch {}
    authStorage.clear()
    queryClient.clear()
  }, [queryClient])

  const value = useMemo<AuthContextValue>(
    () => ({ status, login, register, completeRegistration, completeGoogleLogin, logout }),
    [status, login, register, completeRegistration, completeGoogleLogin, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
