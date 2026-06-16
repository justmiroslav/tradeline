import type { ApiErrorBody, TokenOut } from "@/shared/types/api"

import { authStorage } from "./auth-storage"
import { env } from "./env"

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
    this.name = "ApiError"
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH"
  body?: unknown
  auth?: boolean
  signal?: AbortSignal
  timeoutMs?: number
}

let refreshInFlight: Promise<string | null> | null = null

async function tryRefresh(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight

  refreshInFlight = (async () => {
    try {
      const res = await fetch(`${env.apiBaseUrl}/auth/refresh`, {
        method: "POST",
        credentials: "include"
      })
      if (!res.ok) return null
      const data = (await res.json()) as TokenOut
      authStorage.set(data.access_token)
      return data.access_token
    } catch {
      return null
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

async function parseError(res: Response): Promise<ApiError> {
  try {
    const body = (await res.json()) as Partial<ApiErrorBody>
    return new ApiError(res.status, body.error ?? "HTTPError", body.detail ?? res.statusText)
  } catch {
    return new ApiError(res.status, "HTTPError", res.statusText || "Request failed")
  }
}

async function authedFetch(path: string, opts: RequestOptions): Promise<Response> {
  const { method = "GET", body, auth = true, signal, timeoutMs } = opts
  const url = `${env.apiBaseUrl}${path}`
  const reqSignal = signal ?? (timeoutMs != null ? AbortSignal.timeout(timeoutMs) : undefined)

  const exec = (token: string | null) => {
    const headers: Record<string, string> = {}
    if (body !== undefined) headers["Content-Type"] = "application/json"
    if (auth && token) headers["Authorization"] = `Bearer ${token}`
    return fetch(url, {
      method,
      headers,
      credentials: "include",
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: reqSignal
    })
  }

  const token = auth ? authStorage.getAccess() : null
  const res = await exec(token)
  if (res.status !== 401 || !auth || !token) return res

  const fresh = await tryRefresh()
  if (fresh) return exec(fresh)
  authStorage.clear()
  return res
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const res = await authedFetch(path, opts)
  if (!res.ok) throw await parseError(res)
  if (res.status === 204) return undefined as T
  const ct = res.headers.get("content-type") ?? ""
  if (!ct.includes("application/json")) return undefined as T
  return (await res.json()) as T
}

export async function downloadFile(path: string, filename: string): Promise<void> {
  const res = await authedFetch(path, {})
  if (!res.ok) throw await parseError(res)

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
