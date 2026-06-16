import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useTokenPresence } from "@/shared/hooks/useTokenPresence"
import { authStorage } from "@/shared/lib/auth-storage"
import type { UpdateMeIn, UserOut } from "@/shared/types/api"

import { deleteAccountRequest, meRequest, registerResendRequest, updateMeRequest } from "./api"

export const meQueryKey = ["me"] as const

export function useMe() {
  const hasToken = useTokenPresence()
  return useQuery({
    queryKey: meQueryKey,
    queryFn: meRequest,
    enabled: hasToken,
    staleTime: 5 * 60_000,
    retry: 2
  })
}

export function useUpdateMe() {
  const queryClient = useQueryClient()
  return useMutation<UserOut, Error, UpdateMeIn>({
    mutationFn: updateMeRequest,
    onSuccess: (user) => {
      queryClient.setQueryData(meQueryKey, user)
    }
  })
}

export function useResendRegistrationCode() {
  return useMutation<void, Error, string>({
    mutationFn: registerResendRequest
  })
}

export function useDeleteAccount() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, void>({
    mutationFn: deleteAccountRequest,
    onSuccess: () => {
      authStorage.clear()
      queryClient.clear()
    }
  })
}
