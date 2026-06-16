import { useState } from "react"
import { useNavigate } from "react-router-dom"

import { useDeleteAccount, useMe, useUpdateMe } from "@/features/auth"
import { useSubscription } from "@/features/billing"
import { ReviewForm } from "@/features/reviews"
import { cn } from "@/shared/lib/cn"
import { Btn } from "@/shared/ui/Btn"
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog"
import { EditableField } from "@/shared/ui/EditableField"
import { Ico } from "@/shared/ui/Ico"

const ACTIVE_SUBSCRIPTION = ["active", "trialing", "past_due"]

export function GeneralSettings() {
  const { data: user } = useMe()
  const updateMe = useUpdateMe()
  const deleteAccount = useDeleteAccount()
  const { data: subscription } = useSubscription()
  const navigate = useNavigate()
  const [confirmOpen, setConfirmOpen] = useState(false)

  const subscriptionActive = ACTIVE_SUBSCRIPTION.includes(subscription?.status ?? "")

  const onConfirmDelete = () => {
    deleteAccount.mutate(undefined, {
      onSuccess: () => navigate("/", { replace: true }),
      onSettled: () => setConfirmOpen(false)
    })
  }

  const deleteDescription = subscriptionActive
    ? "Your Pro subscription will be cancelled immediately and all connected keys, imported trades, positions and analytics will be permanently removed"
    : "All connected keys, imported trades, positions and analytics will be permanently removed"

  return (
    <div className="flex flex-col gap-4 min-h-72">
      <section className="rounded-xl border border-line bg-bg-1 p-5 shadow-card">
        <div className="text-[11.5px] uppercase tracking-[0.08em] text-fg-2 mb-3">Profile</div>
        <div className="flex flex-col gap-3">
          <EditableField
            label="Name"
            value={user?.name ?? ""}
            validate={v => (v.length >= 1 && v.length <= 64 ? null : "Use 1 to 64 characters")}
            onSave={v => updateMe.mutateAsync({ name: v })}
            disabled={!user}
          />
          <LockedRow label="Email" value={user?.email ?? "—"} />
        </div>
      </section>

      <ReviewForm />

      <DangerZone
        onDelete={() => setConfirmOpen(true)}
        pending={deleteAccount.isPending}
        note={
          subscriptionActive
            ? "Deleting cancels your Pro subscription — you won't be charged again"
            : "Permanently remove your account, keys and trade history"
        }
        className="mt-auto"
      />

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Delete your account?"
        description={deleteDescription}
        confirmLabel="Delete account"
        pending={deleteAccount.isPending}
        onConfirm={onConfirmDelete}
      />
    </div>
  )
}

function LockedRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 min-h-8">
      <span className="text-[12.5px] text-fg-2">{label}</span>
      <span className="inline-flex items-center gap-1.5 text-[13.5px] text-fg-1 mono leading-none">
        <Ico.Lock width={12} height={12} className="text-fg-3 translate-y-0.5" />
        {value}
      </span>
    </div>
  )
}

interface DangerZoneProps {
  onDelete: () => void
  pending: boolean
  note: string
  className?: string
}

function DangerZone({ onDelete, pending, note, className }: DangerZoneProps) {
  return (
    <div className={cn("rounded-xl border border-loss-bg bg-loss-bg/30 p-5 shadow-card", className)}>
      <div className="text-[11.5px] uppercase tracking-[0.08em] text-loss mb-2.5 font-medium">
        Danger zone
      </div>
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex flex-col gap-0.5">
          <span className="text-[13.5px] text-fg-0 font-medium">Delete account</span>
          <span className="text-[12px] text-fg-2">{note}</span>
        </div>
        <Btn kind="danger" size="md" onClick={onDelete} disabled={pending}>
          {pending ? "Deleting…" : "Delete account"}
        </Btn>
      </div>
    </div>
  )
}
