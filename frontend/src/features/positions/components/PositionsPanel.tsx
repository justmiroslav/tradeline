import { type MouseEvent, type ReactNode, useState } from "react"

import { JOURNAL_PAGE_SIZE, JournalPanel, useJournalControls } from "@/features/journal"
import type { PositionOut } from "@/shared/types/api"

import type { ListPositionsParams } from "../api"
import { exportPositionsCsv } from "../api"
import { POSITION_COLUMNS } from "../columns"
import { usePositions } from "../hooks"
import { PositionPopup } from "./PositionPopup"

interface OpenPopup {
  position: PositionOut
  x: number
  y: number
}

interface PositionsPanelProps {
  listFilters: ListPositionsParams
  active: boolean
  filtersBar: ReactNode
  viewSwitch?: ReactNode
}

export function PositionsPanel({ listFilters, active, filtersBar, viewSwitch }: PositionsPanelProps) {
  const [popups, setPopups] = useState<OpenPopup[]>([])
  const controls = useJournalControls(listFilters, () => exportPositionsCsv(listFilters))
  const query = usePositions({ ...listFilters, page: controls.page, size: JOURNAL_PAGE_SIZE })

  const open = (p: PositionOut, e: MouseEvent) => {
    setPopups(prev => {
      if (prev.some(o => o.position.id === p.id)) return prev
      const x = Math.max(12, Math.min(e.clientX, window.innerWidth - 372))
      const y = Math.max(12, Math.min(e.clientY + 10, window.innerHeight - 240))
      return [...prev, { position: p, x, y }]
    })
  }
  const close = (id: string) => setPopups(prev => prev.filter(o => o.position.id !== id))
  const openIds = new Set(popups.map(o => o.position.id))

  return (
    <>
      <JournalPanel<PositionOut>
        query={query}
        columns={POSITION_COLUMNS}
        rowKey={p => p.id}
        controls={controls}
        active={active}
        noun="position"
        nounPlural="positions"
        emptyHint="Positions are built from your trades as soon as a key finishes syncing"
        filtersBar={filtersBar}
        viewSwitch={viewSwitch}
        onRowClick={open}
        isRowActive={p => openIds.has(p.id)}
      />
      {popups.map(o => (
        <PositionPopup key={o.position.id} position={o.position} initialX={o.x} initialY={o.y} onClose={() => close(o.position.id)} />
      ))}
    </>
  )
}
