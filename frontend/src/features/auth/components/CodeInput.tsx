import { type ClipboardEvent, type KeyboardEvent, useEffect, useRef } from "react"

import { cn } from "@/shared/lib/cn"

interface CodeInputProps {
  length: number
  value: string
  onChange: (code: string) => void
  onComplete: (code: string) => void
  disabled?: boolean
  invalid?: boolean
}

export function CodeInput({ length, value, onChange, onComplete, disabled, invalid }: CodeInputProps) {
  const refs = useRef<(HTMLInputElement | null)[]>([])
  const activeIndex = Math.min(value.length, length - 1)

  useEffect(() => {
    if (!disabled && value.length > 0) refs.current[activeIndex]?.focus()
  }, [activeIndex, disabled, value.length])

  const fill = (digits: string) => {
    const next = digits.slice(0, length)
    onChange(next)
    if (next.length === length) onComplete(next)
  }

  const handleChange = (raw: string) => {
    const digits = raw.replace(/\D/g, "")
    if (digits) fill(value + digits)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && value.length > 0) {
      e.preventDefault()
      onChange(value.slice(0, -1))
    }
  }

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const digits = e.clipboardData.getData("text").replace(/\D/g, "")
    if (digits) fill(digits)
  }

  return (
    <div className="flex items-center gap-2" role="group" aria-label="Verification code">
      {Array.from({ length }, (_, i) => (
        <input
          key={i}
          ref={el => { refs.current[i] = el }}
          value={value[i] ?? ""}
          onChange={e => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          onFocus={() => refs.current[activeIndex]?.focus()}
          disabled={disabled}
          inputMode="numeric"
          autoComplete={i === 0 ? "one-time-code" : "off"}
          aria-label={`Digit ${i + 1} of ${length}`}
          className={cn(
            "flex-1 min-w-0 h-13 rounded-lg bg-bg-2 border text-center text-[20px] font-semibold text-fg-0 mono tnum",
            "outline-none transition-colors focus:border-accent disabled:opacity-50",
            invalid ? "border-loss" : "border-line"
          )}
        />
      ))}
    </div>
  )
}
