import { useState } from "react"
import { useSearchParams } from "react-router-dom"

import { TopBar } from "@/app/shell/TopBar"
import { GeneralSettings } from "@/features/account"
import { BillingPanel } from "@/features/billing"
import { Segmented } from "@/shared/ui/Segmented"

type Section = "general" | "billing"

const SECTION_KEY = "tl:settings-section"

function initialSection(tab: string | null): Section {
  if (tab === "billing" || tab === "general") return tab
  return localStorage.getItem(SECTION_KEY) === "billing" ? "billing" : "general"
}

export default function Settings() {
  const [params] = useSearchParams()
  const [section, setSection] = useState<Section>(() => initialSection(params.get("tab")))

  const choose = (next: Section) => {
    setSection(next)
    localStorage.setItem(SECTION_KEY, next)
  }

  return (
    <>
      <TopBar title="Settings" />
      <div className="flex-1 min-h-0 overflow-y-auto p-4 sm:p-7 max-w-3xl">
        <div className="mb-6">
          <Segmented
            value={section}
            onChange={choose}
            options={[
              { value: "general", label: "General" },
              { value: "billing", label: "Billing" }
            ]}
            ariaLabel="Settings section"
            variant="flat"
            size="sm"
          />
        </div>
        <div>
          {section === "general" ? <GeneralSettings /> : <BillingPanel />}
        </div>
      </div>
    </>
  )
}
