import { EXCHANGE_CAPS } from "@/shared/lib/exchange-caps"
import type { ApiKeyOut } from "@/shared/types/api"
import { ExchangeMark } from "@/shared/ui/ExchangeMark"
import { TwoColumnPanel } from "@/shared/ui/TwoColumnPanel"

import { useApiKeys } from "../hooks"
import { KeyStatusPill } from "./KeyStatusPill"

const MAX = 3

export function ApiKeysOverview() {
  const keys = (useApiKeys().data ?? []).slice(0, MAX)

  return (
    <TwoColumnPanel
      title="API keys"
      left={<KeyList keys={keys} />}
      linkTo="/dashboard/keys"
      linkLabel="API keys →"
    />
  )
}

function KeyList({ keys }: { keys: ApiKeyOut[] }) {
  if (keys.length === 0) {
    return <div className="text-[13px] text-fg-3 py-1">No keys connected yet</div>
  }
  return (
    <ul className="flex flex-col gap-3">
      {keys.map(k => (
        <li key={k.id} className="flex items-center gap-2 text-[13.5px] min-w-0">
          <ExchangeMark name={k.exchange} size={18} />
          <span className="font-medium text-fg-0 truncate min-w-0 flex-1">{k.label || EXCHANGE_CAPS[k.exchange].name}</span>
          <KeyStatusPill apiKey={k} />
        </li>
      ))}
    </ul>
  )
}
