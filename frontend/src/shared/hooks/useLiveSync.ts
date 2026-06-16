import { useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"

import { useTokenPresence } from "@/shared/hooks/useTokenPresence"
import { openEventStream, type StreamEvent } from "@/shared/lib/stream"

const RECONNECT_BASE_MS = 1_000
const RECONNECT_MAX_MS = 30_000
const COALESCE_MS = 350

export function useLiveSync(): void {
  const hasToken = useTokenPresence()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!hasToken) return

    const controller = new AbortController()
    let stopped = false
    let attempts = 0
    let flushTimer: ReturnType<typeof setTimeout> | null = null
    const pending = new Set<string>()

    const flush = () => {
      flushTimer = null
      const keys = [...pending]
      pending.clear()
      for (const key of keys) void queryClient.invalidateQueries({ queryKey: [key] })
    }

    const schedule = (...keys: string[]) => {
      for (const k of keys) pending.add(k)
      if (flushTimer == null) flushTimer = setTimeout(flush, COALESCE_MS)
    }

    const onEvent = (e: StreamEvent) => {
      if (e.type === "trade") schedule("trades", "positions", "analytics")
      else if (e.type === "sync") schedule("trades", "positions", "analytics", "api-keys")
    }

    const run = async () => {
      let firstConnect = true
      while (!stopped) {
        if (!firstConnect) schedule("trades", "positions", "analytics", "api-keys")
        firstConnect = false
        try {
          await openEventStream(onEvent, controller.signal)
          attempts = 0
        } catch {
          if (stopped || controller.signal.aborted) break
          attempts += 1
        }
        if (stopped) break
        const delay = attempts === 0
          ? RECONNECT_BASE_MS
          : Math.min(RECONNECT_BASE_MS * 2 ** (attempts - 1), RECONNECT_MAX_MS)
        await sleep(delay, controller.signal)
      }
    }

    void run()

    return () => {
      stopped = true
      if (flushTimer != null) clearTimeout(flushTimer)
      controller.abort()
    }
  }, [hasToken, queryClient])
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise(resolve => {
    if (signal.aborted) return resolve()
    const timer = setTimeout(resolve, ms)
    signal.addEventListener("abort", () => { clearTimeout(timer); resolve() }, { once: true })
  })
}
