import { Modal } from "@/shared/ui/Modal"

import { SubscriptionForm } from "./SubscriptionForm"

interface SubscriptionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SubscriptionDialog({ open, onOpenChange }: SubscriptionDialogProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Subscribe to Pro">
      <SubscriptionForm />
    </Modal>
  )
}
