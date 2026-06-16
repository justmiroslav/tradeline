import { useInlineEdit } from "@/shared/hooks/useInlineEdit"
import { cn } from "@/shared/lib/cn"

import { Ico } from "./Ico"
import { Spinner } from "./Spinner"

interface EditableFieldProps {
  label: string
  value: string
  type?: "text" | "email"
  placeholder?: string
  validate?: (next: string) => string | null
  onSave: (next: string) => Promise<unknown>
  disabled?: boolean
}

export function EditableField({
  label, value, type = "text", placeholder, validate, onSave, disabled
}: EditableFieldProps) {
  const { editing, draft, setDraft, error, pending, inputRef, enter, cancel, submit, onKey } =
    useInlineEdit({ value, onSave, validate })

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-4 min-h-8">
        <span className="text-[12.5px] text-fg-2">{label}</span>

        {editing ? (
          <div className="flex items-center gap-1.5 flex-1 max-w-75">
            <input
              ref={inputRef}
              type={type}
              value={draft}
              placeholder={placeholder}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKey}
              disabled={pending}
              className={cn(
                "flex-1 h-8 rounded-md bg-bg-2 border text-[13.5px] text-fg-0 px-2.5 outline-none transition-colors",
                error ? "border-loss" : "border-line focus:border-accent"
              )}
              aria-invalid={!!error}
              aria-label={label}
            />
            <button
              type="button"
              onClick={() => void submit()}
              disabled={pending}
              aria-label="Save"
              className="size-8 rounded-md inline-flex items-center justify-center bg-accent text-accent-fg hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
            >
              {pending
                ? <Spinner size={12} tone="onAccent" />
                : <Ico.Check width={14} height={14} strokeWidth={2.5} />
              }
            </button>
            <button
              type="button"
              onClick={cancel}
              disabled={pending}
              aria-label="Cancel"
              className="size-8 rounded-md inline-flex items-center justify-center text-fg-2 hover:text-fg-0 hover:bg-bg-2 disabled:opacity-40 transition-colors"
            >
              <Ico.X width={14} height={14} />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => { if (!disabled) enter() }}
            onDoubleClick={() => { if (!disabled) enter() }}
            disabled={disabled}
            className="group flex items-center gap-2 text-[13.5px] text-fg-0 mono leading-none hover:text-accent transition-colors disabled:cursor-not-allowed disabled:hover:text-fg-0"
            title="Double-click to edit"
          >
            <span>{value || "—"}</span>
            {!disabled && (
              <Ico.Cog
                width={13}
                height={13}
                className="text-fg-3 opacity-0 group-hover:opacity-100 transition-opacity translate-y-px"
              />
            )}
          </button>
        )}
      </div>

      {error && <span className="text-[11.5px] text-loss self-end">{error}</span>}
    </div>
  )
}
