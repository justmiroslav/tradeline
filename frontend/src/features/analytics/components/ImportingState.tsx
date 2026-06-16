export function ImportingState() {
  return (
    <div className="rounded-2xl border border-line bg-bg-1 p-10 sm:p-12 flex flex-col items-center text-center gap-3 shadow-card">
      <span className="size-2.5 shrink-0 rounded-full bg-accent animate-tl-pulse" aria-hidden />
      <div>
        <h2 className="text-[18px] font-semibold m-0 text-fg-0" style={{ letterSpacing: "-0.02em" }}>
          Importing your trades
        </h2>
        <p className="m-0 mt-1.5 text-[13px] text-fg-1 max-w-105">
          Your dashboard lights up the moment the first trades land. This usually takes a few minutes
        </p>
      </div>
    </div>
  )
}

export function NoTradesYet() {
  return (
    <div className="rounded-2xl border border-line bg-bg-1 p-10 sm:p-12 flex flex-col items-center text-center gap-3 shadow-card">
      <div>
        <h2 className="text-[18px] font-semibold m-0 text-fg-0" style={{ letterSpacing: "-0.02em" }}>
          No trades yet
        </h2>
        <p className="m-0 mt-1.5 text-[13px] text-fg-1 max-w-105">
          We synced your connected accounts and found no trade history yet. Your dashboard fills in automatically as you trade
        </p>
      </div>
    </div>
  )
}
