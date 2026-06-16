import { Component, type ErrorInfo, type ReactNode, useEffect } from "react"
import { useRouteError } from "react-router-dom"

const RELOAD_FLAG = "tl-chunk-reloaded"

function isChunkError(error: unknown): boolean {
  const msg = error instanceof Error ? error.message : String(error ?? "")
  return /dynamically imported module|importing a module script failed|loading chunk|failed to fetch/i.test(msg)
}

function reloadOnceOnStaleChunk(error: unknown): void {
  if (isChunkError(error) && !sessionStorage.getItem(RELOAD_FLAG)) {
    sessionStorage.setItem(RELOAD_FLAG, "1")
    window.location.reload()
  }
}

function Fallback() {
  return (
    <div className="min-h-[60vh] w-full flex flex-col items-center justify-center gap-4 px-6 text-center">
      <div className="text-[15px] font-semibold text-fg-0">Something went wrong</div>
      <p className="text-[13px] text-fg-2 max-w-sm m-0 leading-relaxed">
        An unexpected error occurred. Reloading the page usually clears it
      </p>
      <button
        type="button"
        onClick={() => window.location.reload()}
        className="h-10 px-5 rounded-lg bg-accent text-accent-fg text-[13.5px] font-semibold cursor-pointer hover:opacity-90 transition-opacity"
      >
        Reload
      </button>
    </div>
  )
}

export function RouteError() {
  const error = useRouteError()
  useEffect(() => { reloadOnceOnStaleChunk(error) }, [error])
  return <Fallback />
}

interface BoundaryProps {
  children: ReactNode
}

export class ErrorBoundary extends Component<BoundaryProps, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError(): { failed: boolean } {
    return { failed: true }
  }

  componentDidCatch(error: Error, _info: ErrorInfo): void {
    reloadOnceOnStaleChunk(error)
  }

  render(): ReactNode {
    return this.state.failed ? <Fallback /> : this.props.children
  }
}
