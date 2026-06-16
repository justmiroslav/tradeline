import { formatDate, formatPrice } from "@/shared/lib/format"
import { Ico } from "@/shared/ui/Ico"
import { Pill, type PillTone } from "@/shared/ui/Pill"

import type { InvoiceOut } from "../types"

const STATUS_TONE: Record<string, PillTone> = {
  paid: "profit",
  open: "warn",
  draft: "neutral",
  void: "neutral",
  uncollectible: "loss"
}

export function InvoiceHistory({ invoices }: { invoices: InvoiceOut[] }) {
  if (invoices.length === 0) {
    return <div className="text-[13px] text-fg-2 py-2">No invoices yet</div>
  }

  return (
    <div className="relative flex-1 min-h-0">
      <ul className="absolute inset-0 overflow-y-auto [scrollbar-gutter:stable] m-0 py-0 pl-0 pr-3 list-none flex flex-col divide-y divide-line">
        {invoices.map(inv => {
          const href = inv.invoice_pdf ?? inv.hosted_invoice_url
          return (
            <li key={inv.id} className="flex items-center gap-3 py-2.5 first:pt-0">
              <span className="whitespace-nowrap text-[13px] text-fg-1">{formatDate(inv.created)}</span>
              <span className="ml-auto mono tnum text-[13px] text-fg-0 whitespace-nowrap">{formatPrice(inv.amount_paid)}</span>
              <span className="shrink-0 flex justify-center">
                <Pill tone={STATUS_TONE[inv.status ?? ""] ?? "neutral"}>{inv.status ?? "—"}</Pill>
              </span>
              {href ? (
                <a
                  href={href}
                  target="_blank"
                  rel="noreferrer"
                  aria-label="Download invoice"
                  className="size-7 shrink-0 rounded-md inline-flex items-center justify-center text-fg-2 hover:text-fg-0 hover:bg-bg-2 transition-colors cursor-pointer"
                >
                  <Ico.Download width={14} height={14} />
                </a>
              ) : (
                <span className="size-7 shrink-0" aria-hidden />
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
