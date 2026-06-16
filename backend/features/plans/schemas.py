from pydantic import BaseModel

from domain.enums import PlanTier

class PlanOut(BaseModel):
    tier: PlanTier
    api_keys_limit: int | None
    trade_history_months: int
    ai_insight_cooldown_hours: int
    priority_rate_limit: bool
    price_monthly_cents: int
    price_yearly_cents: int
