import { useDashboardNav } from "@/app/shell/dashboard-nav"
import { Ico } from "@/shared/ui/Ico"
import { ThemeToggle } from "@/shared/ui/ThemeToggle"

interface TopBarProps {
  title: string
}

export function TopBar({ title }: TopBarProps) {
  const { setOpen } = useDashboardNav()

  return (
    <header className="shrink-0 flex items-center gap-3 px-4 sm:px-7 h-14 border-b border-line bg-bg-1">
      <button
        type="button"
        aria-label="Open navigation"
        onClick={() => setOpen(true)}
        className="lg:hidden size-8 rounded-md border border-line bg-bg-2 text-fg-1 hover:text-fg-0 inline-flex items-center justify-center transition-colors shrink-0 cursor-pointer"
      >
        <Ico.List width={16} height={16} />
      </button>

      <h1 className="min-w-0 shrink text-[18px] font-semibold tracking-tight text-fg-0 m-0 truncate">
        {title}
      </h1>

      <div className="ml-auto shrink-0">
        <ThemeToggle size="sm" />
      </div>
    </header>
  )
}
