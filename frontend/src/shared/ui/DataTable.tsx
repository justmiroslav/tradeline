import { type MouseEvent, type PointerEvent as ReactPointerEvent, type ReactNode, useCallback, useEffect, useLayoutEffect, useRef, useState } from "react"

import { cn } from "@/shared/lib/cn"
import { Tooltip } from "@/shared/ui/Tooltip"

export interface Column<T> {
  key: string
  header: ReactNode
  width: string
  hint?: string
  align?: "center" | "end"
  cell: (row: T) => ReactNode
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string
  onRowClick?: (row: T, e: MouseEvent) => void
  isRowActive?: (row: T) => boolean
}

const TRACK = 12
const PAD = 4

interface Thumb {
  show: boolean
  offset: number
  size: number
}

const HIDDEN: Thumb = { show: false, offset: 0, size: 0 }

export function DataTable<T>({ columns, rows, rowKey, onRowClick, isRowActive }: DataTableProps<T>) {
  // identical fixed column widths across trades and positions, so a cell is the same size everywhere
  const template = columns.map(c => c.width).join(" ")

  const clickable = !!onRowClick
  const vpRef = useRef<HTMLDivElement>(null)
  const headRef = useRef<HTMLDivElement>(null)
  const [v, setV] = useState<Thumb>(HIDDEN)
  const [h, setH] = useState<Thumb>(HIDDEN)

  const sync = useCallback(() => {
    const vp = vpRef.current
    if (!vp) return
    // keep the header row exactly as wide as the scrollable body and scroll it in sync
    const headInner = headRef.current?.firstElementChild as HTMLElement | null
    if (headInner) {
      headInner.style.width = `${vp.scrollWidth}px`
      headInner.style.transform = `translate3d(${-vp.scrollLeft}px,0,0)`
    }

    const { scrollTop, scrollHeight, clientHeight, scrollLeft, scrollWidth, clientWidth } = vp
    if (scrollHeight > clientHeight + 1) {
      const travel = clientHeight - 2 * PAD
      const size = Math.max(24, (clientHeight / scrollHeight) * travel)
      const offset = PAD + (scrollTop / (scrollHeight - clientHeight)) * (travel - size)
      setV({ show: true, offset, size })
    } else {
      setV(HIDDEN)
    }
    if (scrollWidth > clientWidth + 1) {
      const travel = clientWidth - 2 * PAD
      const size = Math.max(24, (clientWidth / scrollWidth) * travel)
      const offset = PAD + (scrollLeft / (scrollWidth - clientWidth)) * (travel - size)
      setH({ show: true, offset, size })
    } else {
      setH(HIDDEN)
    }
  }, [])

  useLayoutEffect(() => { sync() }, [sync, rows.length, template])

  useEffect(() => {
    const vp = vpRef.current
    if (!vp) return
    const ro = new ResizeObserver(sync)
    ro.observe(vp)
    if (vp.firstElementChild) ro.observe(vp.firstElementChild)
    window.addEventListener("resize", sync)
    return () => { ro.disconnect(); window.removeEventListener("resize", sync) }
  }, [sync])

  const dragV = (e: ReactPointerEvent) => {
    e.preventDefault()
    const vp = vpRef.current
    if (!vp) return
    const startY = e.clientY, startTop = vp.scrollTop, denom = vp.clientHeight - 2 * PAD - v.size
    const move = (ev: PointerEvent) => {
      if (denom > 0) vp.scrollTop = startTop + ((ev.clientY - startY) / denom) * (vp.scrollHeight - vp.clientHeight)
    }
    const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up) }
    window.addEventListener("pointermove", move)
    window.addEventListener("pointerup", up)
  }

  const dragH = (e: ReactPointerEvent) => {
    e.preventDefault()
    const vp = vpRef.current
    if (!vp) return
    const startX = e.clientX, startLeft = vp.scrollLeft, denom = vp.clientWidth - 2 * PAD - h.size
    const move = (ev: PointerEvent) => {
      if (denom > 0) vp.scrollLeft = startLeft + ((ev.clientX - startX) / denom) * (vp.scrollWidth - vp.clientWidth)
    }
    const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up) }
    window.addEventListener("pointermove", move)
    window.addEventListener("pointerup", up)
  }

  return (
    <div className="w-fit max-w-full max-h-full flex flex-col rounded-xl border border-line bg-bg-1 overflow-hidden">
      <div ref={headRef} className="shrink-0 overflow-hidden bg-bg-2 border-b border-line" style={{ paddingRight: v.show ? TRACK : 0 }}>
        <div
          className="grid items-center gap-4 px-4 py-2 text-[10.5px] uppercase tracking-[0.08em] text-fg-2 font-medium"
          style={{ gridTemplateColumns: template }}
        >
          {columns.map(c => <HeaderCell key={c.key} hint={c.hint} align={c.align}>{c.header}</HeaderCell>)}
        </div>
      </div>

      <div className="flex-1 min-h-0 flex">
        <div ref={vpRef} onScroll={sync} className="tl-noscroll flex-1 min-w-0 overflow-auto">
          <ul className="flex flex-col">
            {rows.map((row, i) => (
              <li
                key={rowKey(row)}
                role={clickable ? "button" : undefined}
                tabIndex={clickable ? 0 : undefined}
                onClick={clickable ? e => onRowClick!(row, e) : undefined}
                onKeyDown={clickable ? e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.currentTarget.click() } } : undefined}
                className={cn(
                  "grid items-center gap-4 px-4 py-2 text-[12.5px]",
                  i !== rows.length - 1 && "border-b border-line",
                  clickable && "cursor-pointer hover:bg-bg-2 transition-colors",
                  isRowActive?.(row) && "bg-bg-2"
                )}
                style={{ gridTemplateColumns: template }}
              >
                {columns.map(c => (
                  <div
                    key={c.key}
                    className={cn("min-w-0", c.align === "center" && "flex justify-center", c.align === "end" && "flex justify-end")}
                  >
                    {c.cell(row)}
                  </div>
                ))}
              </li>
            ))}
          </ul>
        </div>

        <div className={cn("shrink-0 relative select-none", v.show && "border-l border-line")} style={{ width: v.show ? TRACK : 0 }}>
          {v.show && (
            <div
              onPointerDown={dragV}
              className="absolute left-1/2 -translate-x-1/2 w-1 rounded-full bg-line hover:bg-line-strong transition-colors cursor-pointer"
              style={{ top: v.offset, height: v.size }}
            />
          )}
        </div>
      </div>

      {h.show && (
        <div className="shrink-0 relative border-t border-line select-none" style={{ height: TRACK, marginRight: v.show ? TRACK : 0 }}>
          <div
            onPointerDown={dragH}
            className="absolute top-1/2 -translate-y-1/2 h-1 rounded-full bg-line hover:bg-line-strong transition-colors cursor-pointer"
            style={{ left: h.offset, width: h.size }}
          />
        </div>
      )}
    </div>
  )
}

function HeaderCell({ hint, align, children }: { hint?: string; align?: "center" | "end"; children: ReactNode }) {
  const cls = cn("block", align === "center" && "text-center", align === "end" && "text-right")
  if (hint) {
    return (
      <Tooltip content={hint} side="top" align="start">
        <span className={cn(cls, "cursor-help")}>{children}</span>
      </Tooltip>
    )
  }
  return <span className={cls}>{children}</span>
}
