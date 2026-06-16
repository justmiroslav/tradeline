import type { Exchange, MarketType } from "@/shared/types/api"

export interface ExchangeCaps {
  name: string
  markets: string
  marketTypes: MarketType[]
  needsPassphrase: boolean
  unifiedMarkets: boolean
}

export const EXCHANGE_CAPS: Record<Exchange, ExchangeCaps> = {
  binance: { name: "Binance", markets: "Spot · USDT-M Futures", marketTypes: ["spot", "futures"], needsPassphrase: false, unifiedMarkets: false },
  bybit: { name: "Bybit", markets: "Spot · Perpetuals", marketTypes: ["spot", "futures"], needsPassphrase: false, unifiedMarkets: false },
  okx: { name: "OKX", markets: "Spot · Perpetuals", marketTypes: ["spot", "futures"], needsPassphrase: true, unifiedMarkets: true },
  bitget: { name: "Bitget", markets: "Spot · USDT-M Futures", marketTypes: ["spot", "futures"], needsPassphrase: true, unifiedMarkets: false }
}

export const EXCHANGES: Exchange[] = ["binance", "bybit", "okx", "bitget"]
