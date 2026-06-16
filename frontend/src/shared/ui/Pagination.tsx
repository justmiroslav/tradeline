import { Ico } from "@/shared/ui/Ico"

interface PaginationProps {
  page: number
  pages: number
  onPage: (p: number) => void
}

export function Pagination({ page, pages, onPage }: PaginationProps) {
  if (pages <= 1) return null

  return (
    <nav className="flex items-center gap-1.5 text-[11.5px] text-fg-2" aria-label="Pagination">
      <ArrowBtn dir="prev" disabled={page <= 1} onClick={() => onPage(page - 1)} />
      <span className="tnum whitespace-nowrap">
        Page <span className="text-fg-1">{page}</span> of <span className="text-fg-1">{pages}</span>
      </span>
      <ArrowBtn dir="next" disabled={page >= pages} onClick={() => onPage(page + 1)} />
    </nav>
  )
}

function ArrowBtn({ dir, disabled, onClick }: { dir: "prev" | "next"; disabled: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={dir === "prev" ? "Previous page" : "Next page"}
      className="size-7 inline-flex items-center justify-center rounded-lg text-fg-1 hover:bg-bg-2 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
    >
      {dir === "prev" ? <Ico.ArrowL width={13} height={13} /> : <Ico.Arrow width={13} height={13} />}
    </button>
  )
}
