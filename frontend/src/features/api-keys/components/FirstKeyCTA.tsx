import { Btn } from "@/shared/ui/Btn"
import { Ico } from "@/shared/ui/Ico"

interface FirstKeyCTAProps {
  onAddKey: () => void
}

export function FirstKeyCTA({ onAddKey }: FirstKeyCTAProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-line bg-bg-1 p-12 flex flex-col items-center text-center gap-4">
      <div
        className="absolute pointer-events-none inset-0"
        style={{
          background: "radial-gradient(closest-side at 50% 0%, var(--accent-glow), transparent 65%)"
        }}
        aria-hidden
      />
      <div className="relative flex flex-col items-center gap-4">
        <button
          type="button"
          onClick={onAddKey}
          aria-label="Add API key"
          className="size-16 rounded-2xl bg-accent text-accent-fg inline-flex items-center justify-center shadow-pop hover:scale-105 hover:opacity-95 transition-transform duration-150 cursor-pointer"
        >
          <Ico.Plus width={28} height={28} strokeWidth={2.5} />
        </button>
        <div>
          <h2
            className="text-[24px] font-semibold m-0 text-fg-0"
            style={{ letterSpacing: "-0.02em" }}
          >
            Connect your first exchange
          </h2>
          <p className="text-[13.5px] text-fg-1 m-0 mt-1.5 max-w-105">
            Paste a read-only key and your trading history turns into a live dashboard — about three minutes
          </p>
        </div>
        <Btn kind="primary" size="lg" onClick={onAddKey} trailing={<Ico.Arrow width={16} height={16} />}>
          Add API key
        </Btn>
      </div>
    </div>
  )
}
