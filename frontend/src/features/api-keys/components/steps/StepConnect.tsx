import { zodResolver } from "@hookform/resolvers/zod"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { useServerInfo } from "@/features/info"
import { cn } from "@/shared/lib/cn"
import { EXCHANGE_CAPS } from "@/shared/lib/exchange-caps"
import type { MarketType } from "@/shared/types/api"
import { Btn } from "@/shared/ui/Btn"
import type { ExchangeName } from "@/shared/ui/ExchangeMark"
import { Field } from "@/shared/ui/Field"
import { Ico } from "@/shared/ui/Ico"
import { Input } from "@/shared/ui/Input"

export interface ExpectedMarkets {
  spot: boolean
  futures: boolean
}

const baseSchema = z.object({
  label: z.string().max(64, "Too long").optional(),
  api_key: z.string().min(1, "Required").max(256, "Too long"),
  api_secret: z.string().min(1, "Required").max(256, "Too long"),
  passphrase: z.string().max(256, "Too long").optional()
})

export type CredsValues = z.infer<typeof baseSchema>

interface StepConnectProps {
  exchange: ExchangeName
  initial: Partial<CredsValues>
  markets: ExpectedMarkets
  onMarketsChange: (m: ExpectedMarkets) => void
  onBack: () => void
  onSubmit: (values: CredsValues) => void
}

const MARKET_LABEL: Record<MarketType, string> = { spot: "Spot", futures: "Futures" }

export function StepConnect({ exchange, initial, markets, onMarketsChange, onBack, onSubmit }: StepConnectProps) {
  const caps = EXCHANGE_CAPS[exchange]
  const needsPass = caps.needsPassphrase

  const schema = needsPass
    ? baseSchema.extend({ passphrase: z.string().min(1, "Required").max(256, "Too long") })
    : baseSchema

  const form = useForm<CredsValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      label: initial.label ?? "",
      api_key: initial.api_key ?? "",
      api_secret: initial.api_secret ?? "",
      passphrase: initial.passphrase ?? ""
    }
  })

  const marketsSelectable = !caps.unifiedMarkets
  const noneSelected = marketsSelectable && !markets.spot && !markets.futures
  const toggleMarket = (m: MarketType) => onMarketsChange({ ...markets, [m]: !markets[m] })

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3.5" noValidate autoComplete="off">
      <h3 className="text-[18px] font-semibold m-0 text-fg-0" style={{ letterSpacing: "-0.02em" }}>
        Connect {caps.name}
      </h3>

      <Field label="Label (optional)" htmlFor="creds-label" error={form.formState.errors.label?.message}>
        <Input
          id="creds-label"
          autoComplete="off"
          placeholder={`Main · ${caps.name}`}
          invalid={!!form.formState.errors.label}
          {...form.register("label")}
        />
      </Field>

      <div className="grid grid-cols-2 gap-3.5">
        <Field label="API key" htmlFor="creds-api-key" error={form.formState.errors.api_key?.message}>
          <Input
            id="creds-api-key"
            type="password"
            autoComplete="new-password"
            spellCheck={false}
            className="w-full"
            invalid={!!form.formState.errors.api_key}
            {...form.register("api_key")}
          />
        </Field>
        <Field label="API secret" htmlFor="creds-api-secret" error={form.formState.errors.api_secret?.message}>
          <Input
            id="creds-api-secret"
            type="password"
            autoComplete="new-password"
            spellCheck={false}
            className="w-full"
            invalid={!!form.formState.errors.api_secret}
            {...form.register("api_secret")}
          />
        </Field>
      </div>

      {needsPass && (
        <Field
          label="Passphrase"
          htmlFor="creds-passphrase"
          error={form.formState.errors.passphrase?.message}
        >
          <Input
            id="creds-passphrase"
            type="password"
            autoComplete="new-password"
            spellCheck={false}
            className="w-full"
            invalid={!!form.formState.errors.passphrase}
            {...form.register("passphrase")}
          />
        </Field>
      )}

      <WhitelistIpNote exchange={exchange} />

      <div className="flex flex-col gap-1.5">
        <span className="text-[12.5px] font-medium text-fg-1">Markets to sync</span>
        {marketsSelectable ? (
          <div className="flex flex-wrap items-center gap-2.5">
            {caps.marketTypes.map(m => (
              <MarketOption key={m} label={MARKET_LABEL[m]} checked={markets[m]} onToggle={() => toggleMarket(m)} />
            ))}
            {noneSelected && <span className="text-[11.5px] text-warn ml-1">Pick at least one market</span>}
          </div>
        ) : (
          <p className="text-[12px] text-fg-2 leading-relaxed m-0">
            {caps.name} is a unified account, so we sync all its spot and futures activity automatically
          </p>
        )}
      </div>

      <footer className="flex items-center justify-between pt-3.5 border-t border-line">
        <Btn type="button" kind="ghost" size="md" onClick={onBack} leading={<Ico.ArrowL width={14} height={14} />}>
          Back
        </Btn>
        <Btn type="submit" kind="primary" size="md" disabled={noneSelected} trailing={<Ico.Arrow width={14} height={14} />}>
          Validate key
        </Btn>
      </footer>

      <ReadOnlyShieldNote />
    </form>
  )
}

function WhitelistIpNote({ exchange }: { exchange: ExchangeName }) {
  const info = useServerInfo()
  const ips = info.data?.whitelist_ips ?? []
  const [copied, setCopied] = useState(false)

  const joined = ips.join(exchange === "binance" ? " " : ",")

  const onCopy = async () => {
    if (!joined) return
    try {
      await navigator.clipboard.writeText(joined)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      return
    }
  }

  return (
    <div className="flex flex-col gap-2 px-3.5 py-3 rounded-lg bg-warn-bg border border-warn/30">
      <div className="flex items-start gap-2">
        <Ico.Warn width={14} height={14} className="text-warn shrink-0 mt-0.5" />
        <div className="flex flex-col gap-0.5">
          <span className="text-[12px] font-semibold text-fg-0">Allow our IP{ips.length > 1 ? "s" : ""} on the exchange first</span>
          <span className="text-[11.5px] text-fg-2 leading-relaxed">
            Paste {ips.length > 1 ? "these" : "this"} into the key's IP whitelist — {exchange === "binance" ? "Binance wants them space-separated" : "comma-separated, no spaces"}
          </span>
        </div>
      </div>
      {info.isPending ? (
        <div className="h-8 rounded-md bg-bg-1 border border-line animate-tl-pulse" aria-hidden />
      ) : ips.length > 0 ? (
        <div className="flex items-center gap-2">
          <code className="flex-1 min-w-0 px-2.5 py-1.5 rounded-md bg-bg-1 border border-line mono tnum text-[12.5px] text-fg-0 select-all whitespace-nowrap overflow-x-auto tl-scroll-thin">
            {joined}
          </code>
          <button
            type="button"
            onClick={onCopy}
            className="h-8 px-2.5 rounded-md bg-bg-1 border border-line text-[11.5px] text-fg-1 hover:text-fg-0 hover:bg-bg-2 transition-colors inline-flex items-center gap-1.5 cursor-pointer shrink-0"
            aria-label="Copy IPs"
          >
            {copied
              ? <><Ico.Check width={12} height={12} className="text-profit" />Copied</>
              : <><Ico.Copy width={12} height={12} />Copy</>
            }
          </button>
        </div>
      ) : (
        <p className="text-[11.5px] text-fg-2 m-0">
          Set <code className="mono text-[11px]">PROXY_POOL_CSV</code> in <code className="mono text-[11px]">backend/.env</code> — the proxy IPs to whitelist will appear here
        </p>
      )}
    </div>
  )
}

function ReadOnlyShieldNote() {
  return (
    <div className="flex items-start gap-2.5 px-3.5 py-2.5 rounded-lg bg-bg-2 border border-line">
      <Ico.Shield width={15} height={15} className="text-accent shrink-0 mt-px" />
      <p className="text-[12px] text-fg-1 leading-relaxed m-0">
        Read-only keys only — we reject anything with trade or withdraw access
      </p>
    </div>
  )
}

interface MarketOptionProps {
  label: string
  checked: boolean
  onToggle: () => void
}

function MarketOption({ label, checked, onToggle }: MarketOptionProps) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      onClick={onToggle}
      className={cn(
        "flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-left transition-colors cursor-pointer",
        checked ? "bg-accent-glow border-accent" : "bg-bg-2 border-line hover:border-line-strong"
      )}
    >
      <span
        className={cn(
          "size-[18px] rounded-[5px] inline-flex items-center justify-center shrink-0 transition-colors",
          checked ? "bg-accent text-accent-fg" : "bg-bg-1 border border-line-strong"
        )}
      >
        {checked && <Ico.Check width={12} height={12} strokeWidth={3} />}
      </span>
      <span className="text-[13.5px] font-medium text-fg-0">{label}</span>
    </button>
  )
}
