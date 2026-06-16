import { type PointerEvent as ReactPointerEvent, useRef, useState } from "react"
import { createPortal } from "react-dom"

import type { PositionOut } from "@/shared/types/api"
import { Ico } from "@/shared/ui/Ico"

import { PositionDetail } from "./PositionDetail"

interface PositionPopupProps {
  position: PositionOut
  initialX: number
  initialY: number
  onClose: () => void
}

export function PositionPopup({ position, initialX, initialY, onClose }: PositionPopupProps) {
  const [pos, setPos] = useState({ x: initialX, y: initialY })
  const start = useRef({ px: 0, py: 0, ox: 0, oy: 0 })

  const onPointerDown = (e: ReactPointerEvent) => {
    e.preventDefault()
    start.current = { px: e.clientX, py: e.clientY, ox: pos.x, oy: pos.y }
    const onMove = (ev: PointerEvent) => setPos({
      x: start.current.ox + ev.clientX - start.current.px,
      y: start.current.oy + ev.clientY - start.current.py
    })
    const onUp = () => {
      window.removeEventListener("pointermove", onMove)
      window.removeEventListener("pointerup", onUp)
    }
    window.addEventListener("pointermove", onMove)
    window.addEventListener("pointerup", onUp)
  }

  return createPortal(
    <div
      style={{ position: "fixed", left: pos.x, top: pos.y, zIndex: 60 }}
      className="rounded-xl border border-line bg-bg-1 tl-pop-shadow animate-tl-fade"
    >
      <button
        type="button"
        onClick={onClose}
        aria-label="Close"
        className="absolute top-2.5 right-2.5 z-10 size-6 rounded-md inline-flex items-center justify-center text-fg-3 hover:text-fg-0 hover:bg-bg-2 transition-colors cursor-pointer"
      >
        <Ico.X width={13} height={13} />
      </button>
      <PositionDetail position={position} dragHandle={{ onPointerDown, className: "cursor-move select-none" }} />
    </div>,
    document.body
  )
}
