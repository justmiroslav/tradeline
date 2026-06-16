import * as Dialog from "@radix-ui/react-dialog"

import { formatNumber } from "@/shared/lib/format"
import { Btn } from "@/shared/ui/Btn"
import { Ico } from "@/shared/ui/Ico"
import { Spinner } from "@/shared/ui/Spinner"

interface ExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  noun: string
  nounPlural: string
  total: number
  active: boolean
  pending: boolean
  error: string | null
  onConfirm: () => void
}

export function ExportDialog({ open, onOpenChange, noun, nounPlural, total, active, pending, error, onConfirm }: ExportDialogProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-bg-0/70 backdrop-blur-sm z-40 data-[state=open]:animate-tl-fade" />
        <Dialog.Content
          aria-describedby={undefined}
          className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-104 max-w-[calc(100vw-32px)] bg-bg-1 border border-line rounded-2xl shadow-pop z-50 p-6 flex flex-col gap-4 outline-none data-[state=open]:animate-tl-fade"
        >
          <div className="flex items-start gap-3">
            <span className="size-10 rounded-xl bg-accent-glow text-accent inline-flex items-center justify-center shrink-0">
              <Ico.Download width={18} height={18} />
            </span>
            <div className="min-w-0">
              <Dialog.Title className="text-[15px] font-semibold m-0 text-fg-0">Export CSV</Dialog.Title>
              <p className="text-[12.5px] text-fg-1 m-0 mt-1 leading-relaxed">
                {active
                  ? `Exports the ${nounPlural} matching the filters currently applied above — adjust the filters to change what's included`
                  : `Exports your full ${noun} history — apply filters above first to narrow it down`}
              </p>
            </div>
          </div>

          <div className="text-[12.5px] text-fg-2 px-3.5 py-2.5 rounded-lg bg-bg-2 border border-line">
            <span className="mono tnum text-fg-0">{formatNumber(total)}</span> {total === 1 ? noun : nounPlural} will be exported
          </div>

          {error && <p className="text-[12px] text-loss m-0">{error}</p>}

          <footer className="flex items-center justify-end gap-2 pt-1">
            <Btn kind="ghost" size="md" onClick={() => onOpenChange(false)} disabled={pending}>Cancel</Btn>
            <Btn
              kind="primary"
              size="md"
              onClick={onConfirm}
              disabled={pending || total === 0}
              leading={pending
                ? <Spinner size={14} tone="onAccent" />
                : <Ico.Download width={14} height={14} />}
            >
              {pending ? "Preparing…" : "Download CSV"}
            </Btn>
          </footer>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
