import * as DropdownMenu from "@radix-ui/react-dropdown-menu"
import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"
import { Ico } from "@/shared/ui/Ico"

import { FILTER_TRIGGER_BASE } from "./filterTrigger"

export interface FilterOption<T extends string> {
  value: T
  label: string
  icon?: ReactNode
}

interface FilterDropdownProps<T extends string> {
  value: T
  options: FilterOption<T>[]
  onChange: (value: T) => void
  ariaLabel: string
}

export function FilterDropdown<T extends string>({ value, options, onChange, ariaLabel }: FilterDropdownProps<T>) {
  const current = options.find(o => o.value === value) ?? options[0]

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        aria-label={ariaLabel}
        className={cn(FILTER_TRIGGER_BASE, "text-fg-2 hover:text-fg-0 hover:bg-bg-2")}
      >
        {current.icon}
        <span className="whitespace-nowrap">{current.label}</span>
        <Ico.Chevron width={11} height={11} className="text-fg-3 group-data-[state=open]:rotate-180 transition-transform" />
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          sideOffset={6}
          className="min-w-(--radix-dropdown-menu-trigger-width) rounded-lg border border-line bg-bg-1 shadow-pop overflow-hidden z-50 p-1"
        >
          {options.map(o => (
            <DropdownMenu.Item
              key={o.value}
              onSelect={() => onChange(o.value)}
              className={cn(
                "flex items-center gap-2 px-2.5 py-2 rounded-md text-[12.5px] outline-none cursor-pointer hover:bg-bg-2 transition-colors",
                o.value === value ? "text-fg-0" : "text-fg-1"
              )}
            >
              {o.icon}
              <span className="flex-1 whitespace-nowrap">{o.label}</span>
              {o.value === value && <Ico.Check width={13} height={13} className="text-accent shrink-0" />}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
