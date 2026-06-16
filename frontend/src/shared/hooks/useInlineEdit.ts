import { type KeyboardEvent, useEffect, useRef, useState } from "react"

import { ApiError } from "@/shared/lib/api"

interface UseInlineEditOptions {
  value: string
  onSave: (next: string) => Promise<unknown>
  validate?: (next: string) => string | null
}

export function useInlineEdit({ value, onSave, validate }: UseInlineEditOptions) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!editing) setDraft(value)
  }, [value, editing])

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus()
      inputRef.current?.select()
    }
  }, [editing])

  const enter = () => {
    setDraft(value)
    setError(null)
    setEditing(true)
  }

  const cancel = () => {
    setDraft(value)
    setError(null)
    setEditing(false)
  }

  const submit = async () => {
    const trimmed = draft.trim()
    if (trimmed === value) {
      cancel()
      return
    }
    if (validate) {
      const msg = validate(trimmed)
      if (msg) {
        setError(msg)
        return
      }
    }
    setPending(true)
    setError(null)
    try {
      await onSave(trimmed)
      setEditing(false)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't save — try again")
    } finally {
      setPending(false)
    }
  }

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      void submit()
    } else if (e.key === "Escape") {
      e.preventDefault()
      cancel()
    }
  }

  return { editing, draft, setDraft, error, pending, inputRef, enter, cancel, submit, onKey }
}
