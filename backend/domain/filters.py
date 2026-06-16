from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.enums import Exchange, MarketType, PositionSide

@dataclass(frozen=True, slots=True)
class AnalyticsFilters:
    date_from: datetime | None = None
    date_to: datetime | None = None
    exchanges: tuple[Exchange, ...] = ()
    market_types: tuple[MarketType, ...] = ()
    symbols: tuple[str, ...] = ()
    setups: tuple[str, ...] = ()
    sides: tuple[PositionSide, ...] = ()
    api_key_ids: tuple[UUID, ...] = ()
