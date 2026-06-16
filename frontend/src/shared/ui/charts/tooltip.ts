import type { TooltipProps } from "recharts"

export interface TooltipRow {
  color: string
  text: string
  dir?: "up" | "down"
}

export interface TooltipModel {
  label?: string
  rows: TooltipRow[]
}

export interface TooltipSignColors {
  profit: string
  loss: string
}

export function buildTooltip<L>(
  p: TooltipProps<number, string>,
  labelFormat: ((value: L) => string) | undefined,
  valueFormat: (value: number) => string,
  fallbackColor: string,
  signColors?: TooltipSignColors
): TooltipModel | null {
  if (!p.active || !p.payload?.length) return null
  return {
    label: labelFormat ? labelFormat(p.label as L) : undefined,
    rows: p.payload.map(entry => {
      const value = (entry.value as number) ?? 0
      if (signColors) {
        return { color: value >= 0 ? signColors.profit : signColors.loss, text: valueFormat(value), dir: value >= 0 ? "up" : "down" as const }
      }
      return { color: entry.color ?? fallbackColor, text: valueFormat(value) }
    })
  }
}
