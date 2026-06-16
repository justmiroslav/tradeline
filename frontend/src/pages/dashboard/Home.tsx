import { useState } from "react"

import { TopBar } from "@/app/shell/TopBar"
import { HomeDashboard } from "@/features/analytics"
import { AddApiKeyDialog, FirstKeyCTA, useApiKeys } from "@/features/api-keys"
import { PlaceholderCard } from "@/shared/ui/PlaceholderCard"
import { QueryError } from "@/shared/ui/QueryError"

export default function Home() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const keysQuery = useApiKeys()
  const keys = keysQuery.data ?? []

  return (
    <>
      <TopBar title="Home" />
      <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-7">
        {keysQuery.isPending ? (
          <PlaceholderCard hint="Loading…" />
        ) : keysQuery.isError ? (
          <QueryError message="Couldn't load your account — check your connection and retry" onRetry={() => keysQuery.refetch()} />
        ) : keys.length === 0 ? (
          <FirstKeyCTA onAddKey={() => setDialogOpen(true)} />
        ) : (
          <HomeDashboard />
        )}
      </div>

      <AddApiKeyDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </>
  )
}
