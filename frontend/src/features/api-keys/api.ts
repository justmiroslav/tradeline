import { request } from "@/shared/lib/api"
import type { ApiKeyIn, ApiKeyOut, ApiKeyValidationResult } from "@/shared/types/api"

export function listApiKeysRequest(): Promise<ApiKeyOut[]> {
  return request<ApiKeyOut[]>("/api-keys/")
}

export function addApiKeyRequest(body: ApiKeyIn): Promise<ApiKeyValidationResult> {
  return request<ApiKeyValidationResult>("/api-keys/", { method: "POST", body })
}

export function recheckApiKeyRequest(keyId: string): Promise<ApiKeyValidationResult> {
  return request<ApiKeyValidationResult>(`/api-keys/${keyId}/recheck`, { method: "POST" })
}

export function updateApiKeyRequest(keyId: string, label: string): Promise<ApiKeyOut> {
  return request<ApiKeyOut>(`/api-keys/${keyId}`, { method: "PATCH", body: { label } })
}

export function deleteApiKeyRequest(keyId: string): Promise<void> {
  return request<void>(`/api-keys/${keyId}`, { method: "DELETE" })
}
