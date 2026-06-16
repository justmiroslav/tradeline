from dataclasses import dataclass

from domain.enums import Exchange, MarketType, PlanTier

ACTIVE_SUBSCRIPTION_STATUSES = frozenset({"active", "trialing", "past_due"})

@dataclass(frozen=True, slots=True)
class PlanConfig:
    api_keys_limit: int | None
    ai_insight_cooldown_hours: int
    priority_rate_limit: bool
    price_monthly_cents: int
    price_yearly_cents: int

PLANS: dict[PlanTier, PlanConfig] = {
    PlanTier.FREE: PlanConfig(
        api_keys_limit=4,
        ai_insight_cooldown_hours=168,
        priority_rate_limit=False,
        price_monthly_cents=0,
        price_yearly_cents=0
    ),
    PlanTier.PRO: PlanConfig(
        api_keys_limit=None,
        ai_insight_cooldown_hours=24,
        priority_rate_limit=True,
        price_monthly_cents=899,
        price_yearly_cents=8999
    )
}

_FREE_HISTORY = {MarketType.SPOT: 3, MarketType.FUTURES: 3}
_PRO_HISTORY = {MarketType.SPOT: 3, MarketType.FUTURES: 3}

TRADE_HISTORY_MONTHS: dict[PlanTier, dict[Exchange, dict[MarketType, int]]] = {
    PlanTier.FREE: {
        Exchange.BINANCE: dict(_FREE_HISTORY),
        Exchange.BYBIT: dict(_FREE_HISTORY),
        Exchange.OKX: dict(_FREE_HISTORY),
        Exchange.BITGET: dict(_FREE_HISTORY)
    },
    PlanTier.PRO: {
        Exchange.BINANCE: dict(_PRO_HISTORY),
        Exchange.BYBIT: dict(_PRO_HISTORY),
        Exchange.OKX: dict(_PRO_HISTORY),
        Exchange.BITGET: dict(_PRO_HISTORY)
    }
}

def get_plan(tier: PlanTier) -> PlanConfig:
    return PLANS[tier]

def history_months(tier: PlanTier, exchange: Exchange, market: MarketType) -> int:
    return TRADE_HISTORY_MONTHS[tier][exchange][market]

def max_history_months(tier: PlanTier) -> int:
    return max(m for markets in TRADE_HISTORY_MONTHS[tier].values() for m in markets.values())

def market_history_months(exchange: Exchange, market: MarketType) -> int:
    return max(TRADE_HISTORY_MONTHS[tier][exchange][market] for tier in TRADE_HISTORY_MONTHS)
