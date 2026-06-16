import { Btn } from "@/shared/ui/Btn"

export function QueryError({ message = "Couldn't load this right now", onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="w-full flex flex-col items-center justify-center gap-3 py-12 px-6 text-center">
      <p className="text-[13px] text-fg-2 max-w-xs m-0 leading-relaxed">{message}</p>
      {onRetry && <Btn kind="secondary" size="sm" onClick={onRetry}>Try again</Btn>}
    </div>
  )
}
