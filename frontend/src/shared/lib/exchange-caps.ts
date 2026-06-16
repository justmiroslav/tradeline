import type { Exchange, MarketType } from "@/shared/types/api"

export interface ExchangeCaps {
  name: string
  markets: string
  marketTypes: MarketType[]
  needsPassphrase: boolean
}

export const EXCHANGE_CAPS: Record<Exchange, ExchangeCaps> = {
  binance: { name: "Binance", markets: "Spot · USDT-M Futures", marketTypes: ["spot", "futures"], needsPassphrase: false },
  bybit: { name: "Bybit", markets: "Spot · Perpetuals", marketTypes: ["spot", "futures"], needsPassphrase: false },
  okx: { name: "OKX", markets: "Spot · Perpetuals", marketTypes: ["spot", "futures"], needsPassphrase: true },
  bitget: { name: "Bitget", markets: "Spot · USDT-M Futures", marketTypes: ["spot", "futures"], needsPassphrase: true }
}

export const EXCHANGES: Exchange[] = ["binance", "bybit", "okx", "bitget"]
