from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field, field_serializer

from domain.enums import Exchange, MarketType, PositionSide, PositionStatus

class PositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    api_key_id: UUID
    exchange: Exchange
    market_type: MarketType
    symbol: str
    side: PositionSide
    status: PositionStatus
    entry_price: Decimal
    exit_price: Optional[Decimal]
    entry_notional: Decimal
    realized_pnl: Decimal
    fees_quote: Decimal
    setup: Optional[str]
    mfe: Optional[Decimal]
    mae: Optional[Decimal]
    trade_count: int
    opened_at: datetime
    closed_at: Optional[datetime]

    @computed_field
    @property
    def size(self) -> float:
        return float(self.entry_notional / self.entry_price) if self.entry_price else 0.0

    @computed_field
    @property
    def net_pnl(self) -> float:
        return float(self.realized_pnl - self.fees_quote)

    @field_serializer("entry_price", "exit_price", "entry_notional", "realized_pnl", "fees_quote", "mfe", "mae")
    def _decimal(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None

class PositionListOut(BaseModel):
    items: list[PositionOut]
    total: int
    page: int
    size: int
    pages: int
