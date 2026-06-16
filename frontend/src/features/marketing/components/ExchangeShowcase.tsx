import { EXCHANGE_CAPS, EXCHANGES } from "@/shared/lib/exchange-caps"
import { ExchangeMark } from "@/shared/ui/ExchangeMark"

export function ExchangeShowcase() {
  return (
    <section className="px-6 sm:px-10 lg:px-14 pt-14 pb-16 sm:pt-20 sm:pb-20 border-t border-line">
      <div className="mb-7">
        <span className="mono text-[11.5px] uppercase tracking-[0.12em] text-fg-2">
          Native integrations
        </span>
        <h2
          className="text-[clamp(24px,3.4vw,32px)] font-semibold m-0 mt-2 text-fg-0"
          style={{ letterSpacing: "-0.025em", textWrap: "balance" }}
        >
          Four exchanges, one source of truth
        </h2>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        {EXCHANGES.map(id => {
          const x = EXCHANGE_CAPS[id]
          return (
            <div
              key={id}
              className="relative p-6 sm:p-7 bg-bg-1 border border-line rounded-2xl overflow-hidden"
            >
              <div
                className="absolute pointer-events-none opacity-70"
                style={{
                  top: -50,
                  right: -50,
                  width: 160,
                  height: 160,
                  borderRadius: 99,
                  background: `radial-gradient(closest-side, color-mix(in oklch, var(--x-${id}) 30%, transparent), transparent 70%)`
                }}
                aria-hidden
              />
              <div className="relative">
                <ExchangeMark name={id} size={44} />
                <div
                  className="mt-4 text-[19px] font-semibold text-fg-0"
                  style={{ letterSpacing: "-0.015em" }}
                >
                  {x.name}
                </div>
                <div className="text-[12.5px] text-fg-2 mt-1.5">{x.markets}</div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
