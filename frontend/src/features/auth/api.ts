import { request } from "@/shared/lib/api"
import type { LoginIn, RegisterIn, TokenOut, UpdateMeIn, UserOut } from "@/shared/types/api"

export function loginRequest(body: LoginIn): Promise<TokenOut> {
  return request<TokenOut>("/auth/login", { method: "POST", body, auth: false })
}

export function googleLoginRequest(credential: string): Promise<TokenOut> {
  return request<TokenOut>("/auth/google", { method: "POST", body: { credential }, auth: false })
}

export function registerRequest(body: RegisterIn): Promise<void> {
  return request<void>("/auth/register", { method: "POST", body, auth: false })
}

export function registerVerifyRequest(email: string, code: string): Promise<TokenOut> {
  return request<TokenOut>("/auth/register/verify", { method: "POST", body: { email, code }, auth: false })
}

export function registerResendRequest(email: string): Promise<void> {
  return request<void>("/auth/register/resend", { method: "POST", body: { email }, auth: false })
}

export function meRequest(): Promise<UserOut> {
  return request<UserOut>("/auth/me", { timeoutMs: 12_000 })
}

export function updateMeRequest(body: UpdateMeIn): Promise<UserOut> {
  return request<UserOut>("/auth/me", { method: "PATCH", body })
}

export function logoutRequest(): Promise<void> {
  return request<void>("/auth/logout", { method: "POST" })
}

export function deleteAccountRequest(): Promise<void> {
  return request<void>("/auth/me", { method: "DELETE" })
}
