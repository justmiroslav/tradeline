import { cn } from "@/shared/lib/cn"
import { EXCHANGE_CAPS, EXCHANGES } from "@/shared/lib/exchange-caps"
import { Btn } from "@/shared/ui/Btn"
import { ExchangeMark, type ExchangeName } from "@/shared/ui/ExchangeMark"
import { Ico } from "@/shared/ui/Ico"

interface StepExchangeProps {
  selected: ExchangeName | null
  onSelect: (ex: ExchangeName) => void
  onContinue: () => void
  onCancel: () => void
}

export function StepExchange({ selected, onSelect, onContinue, onCancel }: StepExchangeProps) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h3
          className="text-[18px] font-semibold m-0 text-fg-0"
          style={{ letterSpacing: "-0.02em" }}
        >
          Pick an exchange
        </h3>
        <p className="text-[13px] text-fg-1 m-0 mt-1">
          We support four exchanges natively
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {EXCHANGES.map(id => {
          const caps = EXCHANGE_CAPS[id]
          const active = selected === id
          return (
            <button
              key={id}
              type="button"
              onClick={() => onSelect(id)}
              aria-pressed={active}
              className={cn(
                "flex items-center gap-3 px-4 py-4 rounded-xl text-left transition-all duration-200",
                active
                  ? "bg-bg-2"
                  : "bg-bg-2 hover:bg-bg-3"
              )}
              style={
                active
                  ? {
                      boxShadow:
                        "0 0 0 2px var(--accent), 0 0 0 6px var(--accent-glow), 0 8px 24px -8px var(--accent-glow)"
                    }
                  : { boxShadow: "0 0 0 1px var(--line)" }
              }
            >
              <ExchangeMark name={id} size={40} />
              <span className="flex-1 min-w-0">
                <span className="block text-[14.5px] font-medium text-fg-0">{caps.name}</span>
                <span className="block text-[11px] text-fg-2 truncate">{caps.markets}</span>
              </span>
            </button>
          )
        })}
      </div>

      <footer className="flex items-center justify-between pt-4 border-t border-line">
        <Btn kind="ghost" size="md" onClick={onCancel}>Cancel</Btn>
        <Btn
          kind="primary"
          size="md"
          disabled={!selected}
          onClick={onContinue}
          trailing={<Ico.Arrow width={14} height={14} />}
        >
          Continue
        </Btn>
      </footer>
    </div>
  )
}
