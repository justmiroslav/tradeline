import type { MouseEvent, ReactNode } from "react"

import { useMediaQuery } from "@/shared/hooks/useMediaQuery"
import { formatNumber } from "@/shared/lib/format"
import { withViewTransition } from "@/shared/lib/viewTransition"
import { Btn } from "@/shared/ui/Btn"
import { type Column, DataTable } from "@/shared/ui/DataTable"
import { ExportDialog } from "@/shared/ui/ExportDialog"
import { Ico } from "@/shared/ui/Ico"
import { Pagination } from "@/shared/ui/Pagination"
import { PlaceholderCard } from "@/shared/ui/PlaceholderCard"
import { QueryError } from "@/shared/ui/QueryError"

import type { JournalControls } from "../useJournalControls"

interface Paginated<T> {
  items: T[]
  total: number
  pages: number
}

interface JournalPanelProps<T> {
  query: { isPending: boolean; isError?: boolean; refetch?: () => void; data: Paginated<T> | undefined }
  columns: Column<T>[]
  rowKey: (row: T) => string
  controls: JournalControls
  active: boolean
  noun: string
  nounPlural: string
  emptyHint: string
  filtersBar: ReactNode
  viewSwitch?: ReactNode
  onRowClick?: (row: T, e: MouseEvent) => void
  isRowActive?: (row: T) => boolean
  split?: number
}

export function JournalPanel<T>({ query, columns, rowKey, controls, active, noun, nounPlural, emptyHint, filtersBar, viewSwitch, onRowClick, isRowActive, split }: JournalPanelProps<T>) {
  const data = query.data
  const items = data?.items ?? []
  const total = data?.total ?? 0
  const pages = data?.pages ?? 0
  const hasRows = !query.isPending && items.length > 0
  const wide = useMediaQuery("(min-width: 1536px)")
  const twoColumns = split != null && items.length > split && wide

  return (
    <div className="flex-1 min-h-0 flex flex-col gap-5 overflow-hidden">
      <div className="shrink-0 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="min-w-0 flex flex-wrap items-center gap-1.5">{filtersBar}</div>
        <div className="sm:ml-auto shrink-0 flex flex-wrap items-center gap-x-6 gap-y-2">
          {viewSwitch}
          <div className="flex items-center gap-2.5">
            {hasRows && (
              <span className="text-[11.5px] text-fg-2 whitespace-nowrap">
                <span className="mono tnum text-fg-1">{items.length}</span> of <span className="mono tnum text-fg-1">{formatNumber(total)}</span> {nounPlural}
              </span>
            )}
            {hasRows && <Pagination page={controls.page} pages={pages} onPage={p => withViewTransition(() => controls.setPage(p))} />}
            <Btn kind="secondary" size="sm" onClick={controls.openExport} disabled={total === 0} leading={<Ico.Download width={13} height={13} />}>
              Export CSV
            </Btn>
          </div>
        </div>
      </div>

      {query.isPending ? (
        <PlaceholderCard hint="Loading…" />
      ) : query.isError ? (
        <QueryError message={`Couldn't load ${nounPlural}`} onRetry={query.refetch} />
      ) : items.length === 0 ? (
        <PlaceholderCard
          title={active ? `No ${nounPlural} match these filters` : `No ${nounPlural} yet`}
          hint={active ? "Try widening or clearing the filters above" : emptyHint}
        />
      ) : (
        <>
          <div className="flex-[7] min-h-0">
            {twoColumns ? (
              <div className="h-full flex justify-center items-start gap-4">
                <DataTable columns={columns} rows={items.slice(0, split)} rowKey={rowKey} onRowClick={onRowClick} isRowActive={isRowActive} />
                <DataTable columns={columns} rows={items.slice(split)} rowKey={rowKey} onRowClick={onRowClick} isRowActive={isRowActive} />
              </div>
            ) : (
              <div className="h-full flex justify-center items-start">
                <DataTable columns={columns} rows={items} rowKey={rowKey} onRowClick={onRowClick} isRowActive={isRowActive} />
              </div>
            )}
          </div>
          <div className="flex-1" aria-hidden />
        </>
      )}

      <ExportDialog
        open={controls.exportOpen}
        onOpenChange={controls.setExportOpen}
        noun={noun}
        nounPlural={nounPlural}
        total={total}
        active={active}
        pending={controls.exporting}
        error={controls.exportError}
        onConfirm={controls.onConfirmExport}
      />
    </div>
  )
}
