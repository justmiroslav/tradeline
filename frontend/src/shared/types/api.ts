export type PlanTier = "free" | "pro"
export type Exchange = "binance" | "bybit" | "okx" | "bitget"
export type MarketType = "spot" | "futures"
export type TradeSide = "buy" | "sell"
export type PositionSide = "long" | "short"
export type PositionStatus = "open" | "closed" | "incomplete"

export interface PlanOut {
  tier: PlanTier
  api_keys_limit: number | null
  trade_history_months: number
  ai_insight_cooldown_hours: number
  priority_rate_limit: boolean
  price_monthly_cents: number
  price_yearly_cents: number
}

export interface TokenOut {
  access_token: string
  token_type: string
}

export interface UserOut {
  id: string
  email: string
  name: string
  plan: PlanTier
  email_verified: boolean
  avatar_url?: string | null
}

export interface RegisterIn {
  email: string
  name: string
  password: string
}

export interface LoginIn {
  email: string
  password: string
}

export interface UpdateMeIn {
  name: string
}

export interface ApiKeyIn {
  exchange: Exchange
  api_key: string
  api_secret: string
  passphrase?: string | null
  label?: string | null
  markets: MarketType[]
}

export interface ApiKeyOut {
  id: string
  exchange: Exchange
  label: string | null
  capabilities: string[]
  account_uid: string | null
  ip_restricted: boolean
  ws_connected: boolean
  last_error: string | null
  last_error_at: string | null
  created_at: string
  suspended: boolean
}

export interface ApiKeyValidationResult {
  id: string
  exchange: Exchange
  capabilities: string[]
  ip_restricted: boolean
  replaced: boolean
  message: string
}

export interface ListFilters {
  date_from?: string
  date_to?: string
  exchanges?: Exchange[]
  market_types?: MarketType[]
  symbols?: string[]
  setups?: string[]
  sides?: PositionSide[]
  api_key_ids?: string[]
}

export interface TradeOut {
  id: string
  position_id: string | null
  exchange: Exchange
  market_type: MarketType
  symbol: string
  side: TradeSide
  price: number
  quantity: number
  fee: number | null
  time: string
}

export interface TradeListOut {
  items: TradeOut[]
  total: number
  page: number
  size: number
  pages: number
}

export interface TradeRangeOut {
  first_trade_at: string | null
  last_trade_at: string | null
}

export interface PositionOut {
  id: string
  api_key_id: string
  exchange: Exchange
  market_type: MarketType
  symbol: string
  side: PositionSide
  status: PositionStatus
  entry_price: number
  exit_price: number | null
  entry_notional: number
  realized_pnl: number
  fees_quote: number
  setup: string | null
  mfe: number | null
  mae: number | null
  trade_count: number
  opened_at: string
  closed_at: string | null
  size: number
  net_pnl: number
}

export interface PositionListOut {
  items: PositionOut[]
  total: number
  page: number
  size: number
  pages: number
}

export interface KpiOut {
  net_pnl: string
  win_rate: number
  profit_factor: number | null
  expectancy: string
  avg_win: string
  avg_loss: string
  total_positions: number
  total_trades: number
  total_volume: string
  total_fees: string
  largest_win: string
  largest_loss: string
  max_drawdown: string
  win_streak: number
  loss_streak: number
}

export interface BucketStat {
  key: string
  net_pnl: string
  count: number
  win_rate: number
  avg_pnl: string
  volume: string
}

export interface DailyPnl {
  date: string
  net_pnl: string
  count: number
}

export interface EquityPoint {
  time: string
  equity: string
}

export interface DurationStat {
  avg_win_minutes: number | null
  avg_loss_minutes: number | null
  median_win_minutes: number | null
  median_loss_minutes: number | null
}

export interface AveragingStat {
  averaged_down_count: number
  averaged_down_net: string
  averaged_down_win_rate: number
  rest_count: number
  rest_net: string
  rest_win_rate: number
}

export interface ExcursionStat {
  avg_mfe: number | null
  avg_mae: number | null
  avg_winner_mfe: number | null
  avg_loser_mae: number | null
}

export interface OpenExposure {
  count: number
  notional: string
}

export interface AnalyticsOut {
  kpis: KpiOut
  by_symbol: BucketStat[]
  by_setup: BucketStat[]
  by_side: BucketStat[]
  by_market: BucketStat[]
  by_hour: BucketStat[]
  by_weekday: BucketStat[]
  daily_pnl: DailyPnl[]
  equity_curve: EquityPoint[]
  duration: DurationStat
  averaging: AveragingStat
  excursion: ExcursionStat
  open_exposure: OpenExposure
  incomplete_count: number
}

export interface AiInsightBody {
  verdict: "profitable" | "breakeven" | "unprofitable"
  headline: string
  edge: string[]
  leaks: string[]
  actions: string[]
}

export interface AiInsightOut {
  insight: AiInsightBody | null
  generated_at: string | null
  next_available_at: string | null
  can_generate: boolean
  cooldown_hours: number
  verified: boolean | null
  feedback: boolean | null
}

export interface ReviewOut {
  id: string
  name: string
  rating: number
  body: string
  created_at: string
}

export interface MyReviewOut {
  rating: number
  body: string
  status: string
}

export interface MarketTickerOut {
  symbol: string
  price: number
  change_pct: number
}

export interface ApiErrorBody {
  error: string
  detail: string
}
