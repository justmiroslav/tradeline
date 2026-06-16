import { Btn } from "@/shared/ui/Btn"
import { Modal } from "@/shared/ui/Modal"

interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel: string
  pending?: boolean
  onConfirm: () => void
}

export function ConfirmDialog({ open, onOpenChange, title, description, confirmLabel, pending = false, onConfirm }: ConfirmDialogProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title={title} closeDisabled={pending}>
      <p className="m-0 -mt-2 text-[13px] text-fg-1 leading-relaxed">{description}</p>
      <footer className="flex items-center justify-end gap-2">
        <Btn kind="ghost" size="md" onClick={() => onOpenChange(false)} disabled={pending}>
          Cancel
        </Btn>
        <Btn kind="danger" size="md" onClick={onConfirm} disabled={pending}>
          {pending ? "Working…" : confirmLabel}
        </Btn>
      </footer>
    </Modal>
  )
}
