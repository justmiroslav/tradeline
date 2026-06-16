import * as RadixTooltip from "@radix-ui/react-tooltip"
import type { ReactNode } from "react"

import { cn } from "@/shared/lib/cn"

interface TooltipProps {
  content: ReactNode
  children: ReactNode
  side?: "top" | "bottom" | "left" | "right"
  align?: "start" | "center" | "end"
  className?: string
}

export function Tooltip({ content, children, side = "top", align = "start", className }: TooltipProps) {
  return (
    <RadixTooltip.Provider delayDuration={150} skipDelayDuration={300}>
      <RadixTooltip.Root>
        <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
        <RadixTooltip.Portal>
          <RadixTooltip.Content
            side={side}
            align={align}
            sideOffset={8}
            collisionPadding={12}
            className={cn(
              "max-w-80 rounded-lg border border-line bg-bg-1 shadow-pop px-3 py-2.5 text-[12px] leading-relaxed text-fg-1 z-50",
              "data-[state=delayed-open]:animate-tl-fade data-[state=instant-open]:animate-tl-fade data-[state=closed]:animate-tl-fade-out",
              className
            )}
          >
            {content}
          </RadixTooltip.Content>
        </RadixTooltip.Portal>
      </RadixTooltip.Root>
    </RadixTooltip.Provider>
  )
}
