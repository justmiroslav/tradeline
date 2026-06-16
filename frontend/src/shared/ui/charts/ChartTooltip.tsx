import type { TooltipModel } from "./tooltip"

export function ChartTooltip({ label, rows }: TooltipModel) {
  return (
    <div className="rounded-lg border border-line bg-bg-1 shadow-pop px-3 py-2 text-[12px] pointer-events-none">
      {label && <div className="text-fg-2 mb-1 mono tnum">{label}</div>}
      {rows.map((r, i) => (
        <div key={i} className="flex items-center gap-2">
          {r.dir
            ? <span className="text-[10px] leading-none shrink-0" style={{ color: r.color }}>{r.dir === "up" ? "▲" : "▼"}</span>
            : <span className="size-2 rounded-full shrink-0" style={{ background: r.color }} />}
          <span className="mono tnum text-fg-0">{r.text}</span>
        </div>
      ))}
    </div>
  )
}
