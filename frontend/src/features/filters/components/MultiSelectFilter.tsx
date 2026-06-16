import * as DropdownMenu from "@radix-ui/react-dropdown-menu"
import { type ReactNode, useState } from "react"

import { cn } from "@/shared/lib/cn"
import { Ico } from "@/shared/ui/Ico"

import { FILTER_TRIGGER_BASE } from "./filterTrigger"

export interface MultiOption<T extends string> {
  value: T
  label: string
  icon?: ReactNode
}

interface MultiSelectFilterProps<T extends string> {
  ariaLabel: string
  allLabel: string
  emptyLabel?: string
  noun: string
  selected: T[]
  options: MultiOption<T>[]
  onChange: (next: T[]) => void
  searchable?: boolean
  searchPlaceholder?: string
}

export function MultiSelectFilter<T extends string>({
  ariaLabel, allLabel, emptyLabel, noun, selected, options, onChange, searchable, searchPlaceholder
}: MultiSelectFilterProps<T>) {
  const [search, setSearch] = useState("")

  const hasOptions = options.length > 0
  const selectedSet = new Set(selected)
  const q = searchable ? search.trim().toLowerCase() : ""
  const visible = q ? options.filter(o => o.label.toLowerCase().includes(q)) : options

  const toggle = (v: T) => onChange(selectedSet.has(v) ? selected.filter(s => s !== v) : [...selected, v])
  const selectAll = () => onChange([...new Set([...selected, ...visible.map(o => o.value)])])
  const clear = () => onChange([])

  const triggerLabel = !hasOptions
    ? (emptyLabel ?? allLabel)
    : selected.length === 0
      ? allLabel
      : selected.length === 1
        ? (options.find(o => o.value === selected[0])?.label ?? `1 ${noun}`)
        : `${selected.length} ${noun}`

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        aria-label={ariaLabel}
        disabled={!hasOptions}
        className={cn(
          FILTER_TRIGGER_BASE,
          "disabled:opacity-50 disabled:cursor-not-allowed",
          selected.length > 0 ? "text-accent bg-accent-glow" : "text-fg-2 hover:text-fg-0 hover:bg-bg-2"
        )}
      >
        <span className="whitespace-nowrap">{triggerLabel}</span>
        <Ico.Chevron width={11} height={11} className="text-fg-3 group-data-[state=open]:rotate-180 transition-transform" />
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          sideOffset={6}
          className={cn("rounded-lg border border-line bg-bg-1 shadow-pop overflow-hidden z-50 flex flex-col", searchable ? "w-80" : "min-w-52")}
        >
          {searchable && (
            <div className="p-2 border-b border-line">
              <div className="relative flex items-center">
                <Ico.Search width={13} height={13} className="absolute left-2.5 text-fg-3 pointer-events-none" />
                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  onKeyDown={e => e.stopPropagation()}
                  placeholder={searchPlaceholder ?? "Search"}
                  autoFocus
                  className="h-8 w-full rounded-md bg-bg-2 border border-line text-[12.5px] text-fg-0 placeholder:text-fg-3 pl-8 pr-2 outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>
          )}

          <div className={cn("p-1 max-h-64 overflow-y-auto [scrollbar-gutter:stable]", searchable && "grid grid-cols-2 gap-x-1 content-start")}>
            {visible.length === 0 ? (
              <div className="text-[12px] text-fg-3 px-2.5 py-2 col-span-2">No matches</div>
            ) : (
              visible.map(o => {
                const on = selectedSet.has(o.value)
                return (
                  <DropdownMenu.CheckboxItem
                    key={o.value}
                    checked={on}
                    onSelect={e => { e.preventDefault(); toggle(o.value) }}
                    className="flex items-center gap-2 px-2 py-1.5 rounded-md text-[12.5px] text-fg-1 outline-none cursor-pointer hover:bg-bg-2 data-highlighted:bg-bg-2 transition-colors"
                  >
                    <span className={cn(
                      "size-4 rounded-[5px] inline-flex items-center justify-center shrink-0 border transition-colors",
                      on ? "bg-accent border-accent text-accent-fg" : "border-line-strong"
                    )}>
                      {on && <Ico.Check width={11} height={11} strokeWidth={3} />}
                    </span>
                    {o.icon}
                    <span className="flex-1 truncate">{o.label}</span>
                  </DropdownMenu.CheckboxItem>
                )
              })
            )}
          </div>

          {(searchable || selected.length > 0) && (
            <div className="flex items-stretch border-t border-line">
              {searchable && (
                <button
                  type="button"
                  onClick={selectAll}
                  disabled={visible.length === 0}
                  className="flex-1 px-3 py-2 text-[12px] text-fg-2 hover:text-fg-0 transition-colors cursor-pointer text-left disabled:opacity-40 disabled:cursor-default"
                >
                  Select all
                </button>
              )}
              <button
                type="button"
                onClick={clear}
                disabled={selected.length === 0}
                className={cn(
                  "px-3 py-2 text-[12px] text-fg-2 hover:text-fg-0 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-default",
                  searchable ? "border-l border-line" : "flex-1 text-left"
                )}
              >
                Clear
              </button>
            </div>
          )}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
