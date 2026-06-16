from datetime import datetime, timezone
from uuid import UUID

from fastapi import Query

from domain.enums import Exchange, MarketType, PositionSide
from domain.filters import AnalyticsFilters

def _utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def filters_query(date_from: datetime | None = Query(None), date_to: datetime | None = Query(None),
                  exchanges: list[Exchange] = Query(default=[]), market_types: list[MarketType] = Query(default=[]),
                  symbols: list[str] = Query(default=[]), setups: list[str] = Query(default=[]),
                  sides: list[PositionSide] = Query(default=[]),
                  api_key_ids: list[UUID] = Query(default=[])) -> AnalyticsFilters:
    return AnalyticsFilters(
        date_from=_utc(date_from), date_to=_utc(date_to),
        exchanges=tuple(exchanges), market_types=tuple(market_types),
        symbols=tuple(symbols), setups=tuple(setups), sides=tuple(sides), api_key_ids=tuple(api_key_ids)
    )
