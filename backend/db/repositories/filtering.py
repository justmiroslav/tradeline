from sqlalchemy import Select

from domain.filters import AnalyticsFilters
from domain.models import Position, Trade

def apply_filters(stmt: Select, model: type[Trade] | type[Position], filters: AnalyticsFilters, date_col=None, setup_col=None, side_col=None) -> Select:
    if filters.exchanges:
        stmt = stmt.where(model.exchange.in_(filters.exchanges))
    if filters.market_types:
        stmt = stmt.where(model.market_type.in_(filters.market_types))
    if filters.symbols:
        stmt = stmt.where(model.symbol.in_(filters.symbols))
    if filters.api_key_ids:
        stmt = stmt.where(model.api_key_id.in_(filters.api_key_ids))
    if date_col is not None and filters.date_from is not None:
        stmt = stmt.where(date_col >= filters.date_from)
    if date_col is not None and filters.date_to is not None:
        stmt = stmt.where(date_col <= filters.date_to)
    if setup_col is not None and filters.setups:
        stmt = stmt.where(setup_col.in_(filters.setups))
    if side_col is not None and filters.sides:
        stmt = stmt.where(side_col.in_(filters.sides))
    return stmt
