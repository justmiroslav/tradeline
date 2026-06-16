import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useTokenPresence } from "@/shared/hooks/useTokenPresence"
import type { ApiKeyIn, ApiKeyOut, ApiKeyValidationResult } from "@/shared/types/api"

import { addApiKeyRequest, deleteApiKeyRequest, listApiKeysRequest, recheckApiKeyRequest, updateApiKeyRequest } from "./api"

export const apiKeysQueryKey = ["api-keys"] as const

interface UseApiKeysOptions {
  pollMs?: number
}

export function useApiKeys({ pollMs = 5_000 }: UseApiKeysOptions = {}) {
  const hasToken = useTokenPresence()
  return useQuery({
    queryKey: apiKeysQueryKey,
    queryFn: listApiKeysRequest,
    enabled: hasToken,
    staleTime: 0,
    refetchInterval: pollMs,
    refetchIntervalInBackground: false
  })
}

export function useAddApiKey() {
  const queryClient = useQueryClient()
  return useMutation<ApiKeyValidationResult, Error, ApiKeyIn>({
    mutationFn: addApiKeyRequest,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: apiKeysQueryKey })
    }
  })
}

export function useRecheckApiKey() {
  const queryClient = useQueryClient()
  return useMutation<ApiKeyValidationResult, Error, string>({
    mutationFn: recheckApiKeyRequest,
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: apiKeysQueryKey })
    }
  })
}

export function useUpdateApiKey() {
  const queryClient = useQueryClient()
  return useMutation<ApiKeyOut, Error, { id: string; label: string }, { prev?: ApiKeyOut[] }>({
    mutationFn: ({ id, label }) => updateApiKeyRequest(id, label),
    onMutate: async ({ id, label }) => {
      await queryClient.cancelQueries({ queryKey: apiKeysQueryKey })
      const prev = queryClient.getQueryData<ApiKeyOut[]>(apiKeysQueryKey)
      queryClient.setQueryData<ApiKeyOut[]>(apiKeysQueryKey, old =>
        old?.map(k => (k.id === id ? { ...k, label } : k))
      )
      return { prev }
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(apiKeysQueryKey, ctx.prev)
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: apiKeysQueryKey })
    }
  })
}

export function useDeleteApiKey() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: deleteApiKeyRequest,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: apiKeysQueryKey })
      void queryClient.invalidateQueries({ queryKey: ["trades"] })
      void queryClient.invalidateQueries({ queryKey: ["analytics"] })
    }
  })
}
