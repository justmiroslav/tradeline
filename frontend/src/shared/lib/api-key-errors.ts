import { ApiError } from "@/shared/lib/api"

export type ApiKeyErrorVariant = {
  title: string
  hint: string
  recoverable: boolean
  goBackTo: "credentials" | "plan" | "close"
}

const variants: Record<string, ApiKeyErrorVariant> = {
  InvalidCredentialsError: {
    title: "Invalid credentials",
    hint: "Copy the API key and secret again — make sure there are no extra spaces",
    recoverable: true,
    goBackTo: "credentials"
  },
  KeyNotReadOnlyError: {
    title: "Key is not read-only",
    hint: "Recreate the key on the exchange with read-only permissions — we reject any key that can trade or withdraw",
    recoverable: true,
    goBackTo: "credentials"
  },
  KeyAccessRestrictedError: {
    title: "Markets restricted",
    hint: "This key doesn't have access to the selected markets — recreate it with those markets enabled, or unselect them",
    recoverable: true,
    goBackTo: "credentials"
  },
  IpNotWhitelistedError: {
    title: "IP not whitelisted",
    hint: "Add this server's IP to the key's whitelist on the exchange, then try again",
    recoverable: true,
    goBackTo: "credentials"
  },
  IpNotRestrictedError: {
    title: "Key has no IP whitelist",
    hint: "Edit the key on the exchange and restrict it to the IP shown in the connect step — unrestricted keys are rejected for your safety",
    recoverable: true,
    goBackTo: "credentials"
  },
  RateLimitError: {
    title: "Rate-limited by exchange",
    hint: "The exchange is throttling us — wait a moment and try again",
    recoverable: true,
    goBackTo: "credentials"
  },
  ExchangeUnavailableError: {
    title: "Exchange unreachable",
    hint: "The exchange API is having trouble — try again in a minute",
    recoverable: true,
    goBackTo: "credentials"
  },
  DuplicateKeyError: {
    title: "Already connected",
    hint: "This API key is already on your account",
    recoverable: false,
    goBackTo: "close"
  },
  PlanLimitError: {
    title: "Plan limit reached",
    hint: "Free plan allows 4 API keys — upgrade to Pro for unlimited connections",
    recoverable: true,
    goBackTo: "plan"
  }
}

const fallback: ApiKeyErrorVariant = {
  title: "Something went wrong",
  hint: "We couldn't validate this key — try again or pick another exchange",
  recoverable: true,
  goBackTo: "credentials"
}

export function mapApiKeyError(err: unknown): ApiKeyErrorVariant {
  if (!(err instanceof ApiError)) return fallback
  return variants[err.code] ?? fallback
}

export function getErrorDetail(err: unknown): string | null {
  if (!(err instanceof ApiError)) return null
  return err.message || null
}

export function getApiKeyErrorCode(err: unknown): string | null {
  return err instanceof ApiError ? err.code : null
}
