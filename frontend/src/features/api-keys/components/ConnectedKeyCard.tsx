import * as DropdownMenu from "@radix-ui/react-dropdown-menu"
import { useState } from "react"

import { useInlineEdit } from "@/shared/hooks/useInlineEdit"
import { accountColor } from "@/shared/lib/account"
import { cn } from "@/shared/lib/cn"
import type { ApiKeyOut } from "@/shared/types/api"
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog"
import { ExchangeMark } from "@/shared/ui/ExchangeMark"
import { Ico } from "@/shared/ui/Ico"
import { Pill } from "@/shared/ui/Pill"
import { Spinner } from "@/shared/ui/Spinner"
import { Tooltip } from "@/shared/ui/Tooltip"

import { useDeleteApiKey, useRecheckApiKey, useUpdateApiKey } from "../hooks"
import { KeyStatusPill } from "./KeyStatusPill"

interface ConnectedKeyCardProps {
  apiKey: ApiKeyOut
}

export function ConnectedKeyCard({ apiKey }: ConnectedKeyCardProps) {
  const deleteKey = useDeleteApiKey()
  const updateKey = useUpdateApiKey()
  const recheckKey = useRecheckApiKey()
  const [confirmOpen, setConfirmOpen] = useState(false)

  const onRename = (label: string) => updateKey.mutateAsync({ id: apiKey.id, label })
  const onRecheck = () => recheckKey.mutate(apiKey.id)
  const onConfirmDisconnect = () => {
    deleteKey.mutate(apiKey.id, { onSettled: () => setConfirmOpen(false) })
  }

  return (
    <div className={cn(
      "flex flex-col gap-2.5 px-4 py-3.5 bg-bg-1 border border-line rounded-xl shadow-card transition-opacity",
      apiKey.suspended && "opacity-60"
    )}>
      <div className="flex items-center gap-2.5">
        <ExchangeMark name={apiKey.exchange} size={30} />
        <div className="flex-1 min-w-0">
          <KeyNameField value={apiKey.label || formatExchangeName(apiKey.exchange)} onSave={onRename} />
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <Capabilities caps={apiKey.capabilities} />
        <KeyStatusPill apiKey={apiKey} />
      </div>

      <div className="flex items-center justify-between gap-2 pt-2 border-t border-line min-h-9.5">
        {apiKey.suspended ? (
          <span className="inline-flex items-center gap-1.5 text-[11px] text-fg-2 min-w-0">
            <Ico.Lock width={11} height={11} className="shrink-0 text-fg-3" />
            <span className="truncate">Suspended — upgrade to Pro to reconnect</span>
          </span>
        ) : apiKey.last_error ? (
          <FooterError message={apiKey.last_error} checking={recheckKey.isPending} onRecheck={onRecheck} />
        ) : (
          <div className="flex items-center gap-3 text-[11px] text-fg-2 min-w-0 overflow-hidden">
            <span className="whitespace-nowrap shrink-0">
              Added <span className="text-fg-1 font-medium tnum">{formatRelative(apiKey.created_at)}</span>
            </span>
            {apiKey.account_uid && <AccountTag uid={apiKey.account_uid} />}
          </div>
        )}
        <ActionsMenu onDisconnect={() => setConfirmOpen(true)} disabled={deleteKey.isPending} />
      </div>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Disconnect this key?"
        description="Its imported trades, positions and analytics contribution will be removed"
        confirmLabel="Disconnect"
        pending={deleteKey.isPending}
        onConfirm={onConfirmDisconnect}
      />
    </div>
  )
}

function FooterError({ message, checking, onRecheck }: { message: string; checking: boolean; onRecheck: () => void }) {
  return (
    <div className="flex items-center gap-2 min-w-0 flex-1">
      <Tooltip content={message}>
        <span className="inline-flex items-center gap-1.5 text-[11px] text-loss min-w-0 flex-1 cursor-help">
          <Ico.Warn width={11} height={11} className="shrink-0" />
          <span className="truncate">{message}</span>
        </span>
      </Tooltip>
      <button
        type="button"
        onClick={onRecheck}
        disabled={checking}
        className="tl-btn-recheck shrink-0 inline-flex items-center gap-1 h-5.5 px-1.5 rounded text-[10.5px] font-medium border disabled:opacity-50 disabled:cursor-default cursor-pointer transition-colors"
      >
        {checking && <Spinner size={8} />}
        {checking ? "Checking…" : "Re-check"}
      </button>
    </div>
  )
}

function AccountTag({ uid }: { uid: string }) {
  return (
    <Tooltip content={<span>Exchange account UID — <span className="mono text-fg-0">{uid}</span></span>}>
      <span
        className="mono text-[10.5px] rounded px-1.5 py-px whitespace-nowrap shrink-0 border cursor-help"
        style={{
          color: accountColor(uid),
          background: accountColor(uid, 0.72, 0.13, 0.1),
          borderColor: accountColor(uid, 0.72, 0.13, 0.3)
        }}
      >
        UID {uid.slice(0, 4)}
      </span>
    </Tooltip>
  )
}

function KeyNameField({ value, onSave }: { value: string; onSave: (label: string) => Promise<unknown> }) {
  const edit = useInlineEdit({ value, onSave, validate: (n) => (n.length > 64 ? "Max 64 characters" : null) })

  if (edit.editing) {
    return (
      <div className="flex items-center gap-1.5">
        <input
          ref={edit.inputRef}
          value={edit.draft}
          maxLength={64}
          onChange={(e) => edit.setDraft(e.target.value)}
          onKeyDown={edit.onKey}
          disabled={edit.pending}
          aria-label="Key name"
          aria-invalid={!!edit.error}
          className={cn(
            "flex-1 min-w-0 h-7 rounded-md bg-bg-2 border text-[13.5px] font-medium text-fg-0 px-2.5 outline-none transition-colors",
            edit.error ? "border-loss" : "border-line focus:border-accent"
          )}
        />
        <button
          type="button"
          onClick={() => void edit.submit()}
          disabled={edit.pending}
          aria-label="Save name"
          className="size-7 rounded-md inline-flex items-center justify-center bg-accent text-accent-fg hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity shrink-0"
        >
          {edit.pending
            ? <Spinner size={12} tone="onAccent" />
            : <Ico.Check width={14} height={14} strokeWidth={2.5} />
          }
        </button>
        <button
          type="button"
          onClick={edit.cancel}
          disabled={edit.pending}
          aria-label="Cancel rename"
          className="size-7 rounded-md inline-flex items-center justify-center text-fg-2 hover:text-fg-0 hover:bg-bg-2 disabled:opacity-40 transition-colors shrink-0"
        >
          <Ico.X width={14} height={14} />
        </button>
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={edit.enter}
      onDoubleClick={edit.enter}
      title="Rename key"
      className="group flex items-center gap-1.5 w-full min-w-0 cursor-pointer text-left"
    >
      <span className="text-[14px] font-semibold text-fg-0 truncate leading-none" style={{ letterSpacing: "-0.01em" }}>
        {value}
      </span>
      <Ico.Cog width={12} height={12} className="text-fg-3 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 translate-y-px" />
    </button>
  )
}

function Capabilities({ caps }: { caps: string[] }) {
  if (caps.length === 0) {
    return <span className="text-[11px] text-fg-3">no markets</span>
  }
  return (
    <div className="flex items-center gap-1.5 flex-wrap min-w-0">
      {caps.map(cap => (
        <Pill key={cap} tone="neutral" className="text-[10.5px] px-1.5 py-0.5 capitalize">
          {cap}
        </Pill>
      ))}
    </div>
  )
}

function ActionsMenu({ onDisconnect, disabled }: { onDisconnect: () => void; disabled: boolean }) {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        className="size-7 -mr-1 rounded-md inline-flex items-center justify-center text-fg-2 hover:text-fg-0 hover:bg-bg-2 transition-colors shrink-0"
        aria-label="Key actions"
      >
        <Ico.More width={15} height={15} />
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={4}
          className="min-w-40 rounded-lg border border-line bg-bg-1 shadow-pop overflow-hidden z-50"
        >
          <DropdownMenu.Item
            disabled={disabled}
            onSelect={(e) => { e.preventDefault(); onDisconnect() }}
            className="flex items-center gap-2.5 px-3.5 py-2.5 text-[12.5px] text-loss outline-none hover:bg-bg-2 cursor-pointer data-disabled:opacity-50"
          >
            <Ico.Trash width={13} height={13} />
            Disconnect
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}

function formatExchangeName(ex: string): string {
  return ex.charAt(0).toUpperCase() + ex.slice(1)
}

function formatRelative(iso: string | null): string {
  if (!iso) return "never"
  const ms = Date.now() - new Date(iso).getTime()
  if (ms < 0 || isNaN(ms)) return "just now"
  const sec = Math.floor(ms / 1000)
  if (sec < 60) return "just now"
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min} min ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} hr ago`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day} d ago`
  const mon = Math.floor(day / 30)
  return `${mon} mo ago`
}
