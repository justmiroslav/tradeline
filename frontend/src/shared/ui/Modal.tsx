import * as Dialog from "@radix-ui/react-dialog"
import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"
import { Ico } from "@/shared/ui/Ico"

interface ModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  children: ReactNode
  className?: string
  closeDisabled?: boolean
}

export function Modal({ open, onOpenChange, title, children, className, closeDisabled = false }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-bg-0/70 backdrop-blur-sm z-40 data-[state=open]:animate-tl-fade data-[state=closed]:animate-tl-fade-out" />
        <Dialog.Content
          aria-describedby={undefined}
          onInteractOutside={(e) => e.preventDefault()}
          className={cn(
            "fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-110 max-w-[calc(100vw-32px)] max-h-[calc(100vh-32px)] overflow-y-auto bg-bg-1 border border-line rounded-2xl shadow-pop z-50 p-7 flex flex-col gap-6 outline-none data-[state=open]:animate-tl-fade data-[state=closed]:animate-tl-fade-out",
            className
          )}
        >
          <header className="flex items-center justify-between gap-4">
            <Dialog.Title className="text-[16px] font-semibold m-0 text-fg-0" style={{ letterSpacing: "-0.015em" }}>
              {title}
            </Dialog.Title>
            <Dialog.Close
              aria-label="Close"
              disabled={closeDisabled}
              className="size-8 rounded-md inline-flex items-center justify-center text-fg-2 hover:text-fg-0 hover:bg-bg-2 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Ico.X width={16} height={16} />
            </Dialog.Close>
          </header>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
