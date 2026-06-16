import { useEffect, useState } from "react"

export interface JournalControls {
  page: number
  setPage: (p: number) => void
  exportOpen: boolean
  setExportOpen: (open: boolean) => void
  exporting: boolean
  exportError: string | null
  openExport: () => void
  onConfirmExport: () => void
}

export function useJournalControls(resetKey: unknown, exportFn: () => Promise<void>): JournalControls {
  const [page, setPage] = useState(1)
  const [exportOpen, setExportOpen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const resetSig = JSON.stringify(resetKey)
  useEffect(() => { setPage(1) }, [resetSig])

  const openExport = () => {
    setExportError(null)
    setExportOpen(true)
  }

  const onConfirmExport = async () => {
    setExporting(true)
    setExportError(null)
    try {
      await exportFn()
      setExportOpen(false)
    } catch (e) {
      setExportError(e instanceof Error ? e.message : "Export failed — please try again")
    } finally {
      setExporting(false)
    }
  }

  return { page, setPage, exportOpen, setExportOpen, exporting, exportError, openExport, onConfirmExport }
}
