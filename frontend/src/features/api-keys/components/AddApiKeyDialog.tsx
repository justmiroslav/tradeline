import { useCallback, useState } from "react"

import type { ApiKeyErrorVariant } from "@/shared/lib/api-key-errors"
import { getApiKeyErrorCode, getErrorDetail, mapApiKeyError } from "@/shared/lib/api-key-errors"
import { EXCHANGE_CAPS } from "@/shared/lib/exchange-caps"
import type { ApiKeyValidationResult, MarketType } from "@/shared/types/api"
import type { ExchangeName } from "@/shared/ui/ExchangeMark"
import { Modal } from "@/shared/ui/Modal"

import { useAddApiKey } from "../hooks"
import { Stepper } from "./Stepper"
import { type CredsValues, type ExpectedMarkets, StepConnect } from "./steps/StepConnect"
import { StepExchange } from "./steps/StepExchange"
import { StepValidation } from "./steps/StepValidation"
import { StepTransition } from "./StepTransition"

type Step = 1 | 2 | 3

type ValidationState =
  | { kind: "pending" }
  | { kind: "success"; result: ApiKeyValidationResult }
  | { kind: "error"; variant: ApiKeyErrorVariant; detail: string | null; code: string | null }

const INITIAL_MARKETS: ExpectedMarkets = { spot: true, futures: true }
const INITIAL_CREDS: Partial<CredsValues> = {}

interface AddApiKeyDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AddApiKeyDialog({ open, onOpenChange }: AddApiKeyDialogProps) {
  const [step, setStep] = useState<Step>(1)
  const [exchange, setExchange] = useState<ExchangeName | null>(null)
  const [markets, setMarkets] = useState<ExpectedMarkets>(INITIAL_MARKETS)
  const [creds, setCreds] = useState<Partial<CredsValues>>(INITIAL_CREDS)
  const [validation, setValidation] = useState<ValidationState>({ kind: "pending" })

  const mutation = useAddApiKey()

  const reset = useCallback(() => {
    setStep(1)
    setExchange(null)
    setMarkets(INITIAL_MARKETS)
    setCreds(INITIAL_CREDS)
    setValidation({ kind: "pending" })
    mutation.reset()
  }, [mutation])

  const handleOpenChange = useCallback((next: boolean) => {
    if (!next && mutation.isPending) return
    onOpenChange(next)
    if (!next) {
      window.setTimeout(reset, 200)
    }
  }, [mutation.isPending, onOpenChange, reset])

  const close = useCallback(() => handleOpenChange(false), [handleOpenChange])

  const onValidate = (values: CredsValues) => {
    if (!exchange) return
    setCreds(values)
    setStep(3)
    setValidation({ kind: "pending" })

    const picked: MarketType[] = []
    if (markets.spot) picked.push("spot")
    if (markets.futures) picked.push("futures")
    const selectedMarkets: MarketType[] = (EXCHANGE_CAPS[exchange].unifiedMarkets || picked.length === 2) ? [] : picked

    mutation.mutate(
      {
        exchange,
        api_key: values.api_key,
        api_secret: values.api_secret,
        passphrase: values.passphrase ?? null,
        label: values.label ?? null,
        markets: selectedMarkets
      },
      {
        onSuccess: (result) => setValidation({ kind: "success", result }),
        onError: (err) => setValidation({
          kind: "error",
          variant: mapApiKeyError(err),
          detail: getErrorDetail(err),
          code: getApiKeyErrorCode(err)
        })
      }
    )
  }

  return (
    <Modal
      open={open}
      onOpenChange={handleOpenChange}
      title="Add API key"
      className="w-145"
      closeDisabled={mutation.isPending}
    >
      <Stepper current={step} />

      <div className="flex-1">
        <StepTransition step={step}>
          {step === 1 && (
            <StepExchange
              selected={exchange}
              onSelect={setExchange}
              onCancel={close}
              onContinue={() => setStep(2)}
            />
          )}
          {step === 2 && exchange && (
            <StepConnect
              exchange={exchange}
              initial={creds}
              markets={markets}
              onMarketsChange={setMarkets}
              onBack={() => setStep(1)}
              onSubmit={onValidate}
            />
          )}
          {step === 3 && exchange && (
            <StepValidation
              state={validation}
              onEditKey={() => setStep(2)}
              onClose={close}
              onDone={close}
            />
          )}
        </StepTransition>
      </div>
    </Modal>
  )
}
