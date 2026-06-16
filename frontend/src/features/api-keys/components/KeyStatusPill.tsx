import type { ApiKeyOut } from "@/shared/types/api"
import { Pill } from "@/shared/ui/Pill"

const RECENT_ADD_MS = 30_000

export function KeyStatusPill({ apiKey }: { apiKey: ApiKeyOut }) {
  if (apiKey.suspended) return <Pill tone="neutral" dot>suspended</Pill>
  if (apiKey.last_error) return <Pill tone="loss" dot>needs attention</Pill>
  const recentlyAdded = Date.now() - new Date(apiKey.created_at).getTime() < RECENT_ADD_MS
  if (apiKey.ws_connected || recentlyAdded) return <Pill tone="profit" dot="live">live</Pill>
  return <Pill tone="warn" dot>connecting</Pill>
}
