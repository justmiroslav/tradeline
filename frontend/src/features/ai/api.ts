import { request } from "@/shared/lib/api"
import { authStorage } from "@/shared/lib/auth-storage"
import { env } from "@/shared/lib/env"
import type { AiInsightOut } from "@/shared/types/api"

export function getAiInsightRequest(): Promise<AiInsightOut> {
  return request<AiInsightOut>("/ai/insight")
}

export async function streamAiInsight(
  onToken: (delta: string) => void,
  onDone: (data: AiInsightOut) => void,
  signal: AbortSignal
): Promise<void> {
  const token = authStorage.getAccess()
  const res = await fetch(`${env.apiBaseUrl}/ai/insight/stream`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token ?? ""}`, Accept: "text/event-stream" },
    credentials: "include",
    signal
  })
  if (!res.ok || !res.body) throw new Error(`stream ${res.status}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true }).replace(/\r/g, "")
    let sep: number
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      let event = "message"
      const data: string[] = []
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim()
        else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""))
      }
      const payload = data.join("\n")
      if (event === "token") onToken(payload)
      else if (event === "done") {
        try { onDone(JSON.parse(payload) as AiInsightOut) } catch { /* keep last good */ }
      }
    }
  }
}

export function generateAiInsightRequest(): Promise<AiInsightOut> {
  return request<AiInsightOut>("/ai/insight", { method: "POST" })
}

export function aiInsightFeedbackRequest(helpful: boolean): Promise<AiInsightOut> {
  return request<AiInsightOut>("/ai/insight/feedback", { method: "POST", body: { helpful } })
}
