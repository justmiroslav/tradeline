import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useState } from "react"

import { useTokenPresence } from "@/shared/hooks/useTokenPresence"
import type { AiInsightBody, AiInsightOut } from "@/shared/types/api"

import { aiInsightFeedbackRequest, generateAiInsightRequest, getAiInsightRequest, streamAiInsight } from "./api"

export const aiInsightKey = ["ai", "insight"] as const

function unescape(raw: string): string {
  try {
    return JSON.parse(`"${raw}"`)
  } catch {
    return raw
  }
}

function readString(acc: string, key: string): string {
  const m = acc.match(new RegExp(`"${key}"\\s*:\\s*"((?:[^"\\\\]|\\\\.)*)`))
  return m ? unescape(m[1]) : ""
}

function readArray(acc: string, key: string): string[] {
  const at = acc.search(new RegExp(`"${key}"\\s*:\\s*\\[`))
  if (at === -1) return []
  const open = acc.indexOf("[", at)
  const close = acc.indexOf("]", open)
  const segment = close === -1 ? acc.slice(open + 1) : acc.slice(open + 1, close)
  const items: string[] = []
  const re = /"((?:[^"\\]|\\.)*)"/g
  let m: RegExpExecArray | null
  while ((m = re.exec(segment)) !== null) items.push(unescape(m[1]))
  return items
}

function parsePartial(acc: string): AiInsightBody {
  const verdict = readString(acc, "verdict")
  return {
    verdict: verdict === "profitable" || verdict === "unprofitable" ? verdict : "breakeven",
    headline: readString(acc, "headline"),
    edge: readArray(acc, "edge"),
    leaks: readArray(acc, "leaks"),
    actions: readArray(acc, "actions")
  }
}

export function useAiInsight() {
  const hasToken = useTokenPresence()
  return useQuery({
    queryKey: aiInsightKey,
    queryFn: getAiInsightRequest,
    enabled: hasToken,
    staleTime: 60_000
  })
}

export function useStreamingInsight() {
  const queryClient = useQueryClient()
  const [streaming, setStreaming] = useState(false)
  const [partial, setPartial] = useState<AiInsightBody | null>(null)
  const [error, setError] = useState<string | null>(null)

  const start = useCallback(async () => {
    setStreaming(true)
    setPartial(null)
    setError(null)
    const controller = new AbortController()
    let acc = ""
    try {
      await streamAiInsight(
        delta => {
          acc += delta
          setPartial(parsePartial(acc))
        },
        data => queryClient.setQueryData(aiInsightKey, data),
        controller.signal
      )
    } catch {
      try {
        queryClient.setQueryData(aiInsightKey, await generateAiInsightRequest())
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not generate insight")
      }
    } finally {
      setStreaming(false)
      setPartial(null)
    }
  }, [queryClient])

  return { start, streaming, partial, error }
}

export function useAiInsightFeedback() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: aiInsightFeedbackRequest,
    onSuccess: (data: AiInsightOut) => queryClient.setQueryData(aiInsightKey, data)
  })
}
