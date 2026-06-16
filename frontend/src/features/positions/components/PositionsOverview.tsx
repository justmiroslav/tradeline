import { Fragment } from "react"

import { PnlCell } from "@/features/journal"
import type { PositionOut } from "@/shared/types/api"
import { ExchangeMark } from "@/shared/ui/ExchangeMark"
import { Pill } from "@/shared/ui/Pill"
import { TwoColumnPanel } from "@/shared/ui/TwoColumnPanel"

import { usePositions } from "../hooks"

const MAX = 3

export function PositionsOverview() {
  const closed = usePositions({ status: "closed", size: MAX }).data?.items ?? []
  const open = usePositions({ status: "open", size: MAX }).data?.items ?? []
  const incomplete = usePositions({ status: "incomplete", size: MAX }).data?.items ?? []
  const showIncomplete = open.length === 0 && incomplete.length > 0

  return (
    <TwoColumnPanel
      title="Positions"
      left={<PositionList items={closed} kind="closed" />}
      right={<PositionList items={showIncomplete ? incomplete : open} kind={showIncomplete ? "incomplete" : "open"} />}
      linkTo="/dashboard/journal"
      linkState={{ view: "positions" }}
      linkLabel="Open in Journal →"
    />
  )
}

function PositionList({ items, kind }: { items: PositionOut[]; kind: "closed" | "open" | "incomplete" }) {
  if (items.length === 0) {
    return <div className="text-[13px] text-fg-3 py-1">{kind === "closed" ? "Nothing closed yet" : "Nothing open"}</div>
  }
  return (
    <div className="grid grid-cols-[auto_minmax(0,1fr)_auto_minmax(56px,1fr)] items-center gap-x-3 gap-y-3 text-[13.5px]">
      {items.map(p => (
        <Fragment key={p.id}>
          <ExchangeMark name={p.exchange} size={18} />
          <span className="font-medium text-fg-0 truncate min-w-0">{p.symbol}</span>
          <Pill tone={p.side === "long" ? "profit" : "loss"} className="justify-self-center capitalize">{p.side}</Pill>
          <span className="justify-self-end">
            {kind === "closed"
              ? <PnlCell value={p.net_pnl} />
              : kind === "incomplete"
                ? <Pill tone="warn">incomplete</Pill>
                : <Pill tone="accent" dot="live">open</Pill>}
          </span>
        </Fragment>
      ))}
    </div>
  )
}
