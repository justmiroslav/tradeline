from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from domain.enums import Exchange, MarketType, TradeSide

class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position_id: Optional[UUID]
    exchange: Exchange
    market_type: MarketType
    symbol: str
    side: TradeSide
    price: Decimal
    quantity: Decimal
    fee: Optional[Decimal]
    time: datetime

    @field_serializer("price", "quantity", "fee")
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None

class TradeListOut(BaseModel):
    items: list[TradeOut]
    total: int
    page: int
    size: int
    pages: int

class TradeRangeOut(BaseModel):
    first_trade_at: Optional[datetime]
    last_trade_at: Optional[datetime]
