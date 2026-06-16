import { authStorage } from "./auth-storage"
import { env } from "./env"

export interface StreamEvent {
  type: string
  data: unknown
}

const FRAME_BOUNDARY = /\r\n\r\n|\n\n|\r\r/

export async function openEventStream(onEvent: (event: StreamEvent) => void, signal: AbortSignal): Promise<void> {
  const token = authStorage.getAccess()
  if (!token) throw new Error("No access token")

  const res = await fetch(`${env.apiBaseUrl}/stream`, {
    headers: { Authorization: `Bearer ${token}`, Accept: "text/event-stream" },
    signal
  })
  if (!res.ok || !res.body) throw new Error(`Stream failed (${res.status})`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let match: RegExpExecArray | null
    while ((match = FRAME_BOUNDARY.exec(buffer)) !== null) {
      const frame = buffer.slice(0, match.index)
      buffer = buffer.slice(match.index + match[0].length)
      const event = parseFrame(frame)
      if (event) onEvent(event)
    }
  }
}

function parseFrame(frame: string): StreamEvent | null {
  let type = "message"
  const dataLines: string[] = []

  for (const line of frame.split(/\r\n|\r|\n/)) {
    if (line === "" || line.startsWith(":")) continue
    const colon = line.indexOf(":")
    const field = colon === -1 ? line : line.slice(0, colon)
    const rest = colon === -1 ? "" : line.slice(colon + 1)
    const value = rest.startsWith(" ") ? rest.slice(1) : rest
    if (field === "event") type = value
    else if (field === "data") dataLines.push(value)
  }

  if (dataLines.length === 0) return null
  const payload = dataLines.join("\n")
  try {
    return { type, data: JSON.parse(payload) }
  } catch {
    return { type, data: payload }
  }
}
