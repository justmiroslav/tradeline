import { useSyncExternalStore } from "react"

import { authStorage } from "@/shared/lib/auth-storage"

const subscribe = (listener: () => void) => authStorage.subscribe(listener)
const getSnapshot = () => !!authStorage.getAccess()
const getServerSnapshot = () => false

export function useTokenPresence(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
