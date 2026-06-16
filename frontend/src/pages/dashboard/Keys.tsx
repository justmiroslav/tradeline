import { useState } from "react"
import { Link } from "react-router-dom"

import { TopBar } from "@/app/shell/TopBar"
import { AddApiKeyDialog, ConnectedKeyCard, FirstKeyCTA, useApiKeys } from "@/features/api-keys"
import { useMe } from "@/features/auth"
import { usePlans } from "@/features/plan"
import { Btn } from "@/shared/ui/Btn"
import { btnClass } from "@/shared/ui/btn-class"
import { Ico } from "@/shared/ui/Ico"
import { PlaceholderCard } from "@/shared/ui/PlaceholderCard"
import { QueryError } from "@/shared/ui/QueryError"

export default function Keys() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const keysQuery = useApiKeys()
  const { data: user } = useMe()
  const { data: plans } = usePlans()
  const keys = keysQuery.data ?? []

  const limit = plans?.find(p => p.tier === user?.plan)?.api_keys_limit ?? null
  const atLimit = limit != null && keys.length >= limit
  const suspendedCount = keys.filter(k => k.suspended).length
  const blocks = Array.from({ length: Math.ceil(keys.length / 4) }, (_, i) => keys.slice(i * 4, i * 4 + 4))

  return (
    <>
      <TopBar title="API keys" />
      <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-7">
        {keysQuery.isPending ? (
          <PlaceholderCard hint="Loading…" />
        ) : keysQuery.isError ? (
          <QueryError message="Couldn't load your keys — check your connection and retry" onRetry={() => keysQuery.refetch()} />
        ) : keys.length === 0 ? (
          <FirstKeyCTA onAddKey={() => setDialogOpen(true)} />
        ) : (
          <section className="flex flex-col gap-3">
            <div className="text-[12.5px] text-fg-2">
              {limit != null
                ? `${keys.filter(k => !k.suspended).length} of ${limit} keys connected${suspendedCount ? ` · ${suspendedCount} suspended` : ""}`
                : `${keys.length} ${keys.length === 1 ? "key" : "keys"} connected`}
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 items-start">
              {blocks.map((block, i) => (
                <ul key={i} className="grid grid-cols-1 sm:grid-cols-2 gap-3 content-start m-0 p-0 list-none">
                  {block.map(k => (
                    <li key={k.id}>
                      <ConnectedKeyCard apiKey={k} />
                    </li>
                  ))}
                </ul>
              ))}
            </div>

            {atLimit ? (
              <PlanLimitNotice limit={limit!} />
            ) : (
              <Btn
                kind="secondary"
                size="md"
                onClick={() => setDialogOpen(true)}
                leading={<Ico.Plus width={14} height={14} />}
                className="self-start"
              >
                Add another key
              </Btn>
            )}
          </section>
        )}
      </div>

      <AddApiKeyDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </>
  )
}

function PlanLimitNotice({ limit }: { limit: number }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3.5 rounded-xl border border-accent/30 bg-accent-glow">
      <span className="size-9 rounded-lg bg-bg-1 text-accent inline-flex items-center justify-center shrink-0">
        <Ico.Crown width={18} height={18} />
      </span>
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-semibold text-fg-0">You've reached the Basic limit of {limit} keys</div>
        <div className="text-[12px] text-fg-2">Upgrade to Pro for unlimited exchange connections</div>
      </div>
      <Link to="/dashboard/settings?tab=billing" className={btnClass("primary", "md")}>
        Upgrade to Pro
      </Link>
    </div>
  )
}
