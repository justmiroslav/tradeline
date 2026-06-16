import type { ReactNode } from "react"
import { Link } from "react-router-dom"

import { Panel } from "@/shared/ui/Panel"

interface TwoColumnPanelProps {
  title: string
  left: ReactNode
  right?: ReactNode
  linkTo: string
  linkLabel: string
  linkState?: Record<string, unknown>
}

export function TwoColumnPanel({ title, left, right, linkTo, linkLabel, linkState }: TwoColumnPanelProps) {
  return (
    <Panel title={title}>
      {right != null ? (
        <div className="@container">
          <div className="grid grid-cols-1 gap-y-3 @sm:grid-cols-2">
            <div className="min-w-0 @sm:pr-4">{left}</div>
            <div className="min-w-0 border-t border-line pt-3 @sm:border-t-0 @sm:pt-0 @sm:border-l @sm:pl-4">{right}</div>
          </div>
        </div>
      ) : (
        <div className="min-w-0">{left}</div>
      )}
      <Link to={linkTo} state={linkState} className="mt-auto pt-4 mx-auto text-[12.5px] text-accent hover:underline">
        {linkLabel}
      </Link>
    </Panel>
  )
}
