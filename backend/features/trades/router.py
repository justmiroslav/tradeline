from datetime import datetime, timedelta, timezone
from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.trade import TradeRepository
from domain.filters import AnalyticsFilters
from domain.models import Trade, User
from domain.plans import max_history_months
from features.analytics.deps import filters_query
from features.trades.schemas import TradeListOut, TradeOut, TradeRangeOut
from shared.csv import csv_response
from shared.deps import get_current_user, get_session

router = APIRouter(prefix="/trades", tags=["trades"])

_CSV_HEADER = ["time", "exchange", "market_type", "symbol", "side", "price", "quantity", "fee"]

def _csv_row(t: Trade) -> list:
    return [
        t.time.isoformat(), t.exchange.value, t.market_type.value, t.symbol, t.side.value,
        str(t.price), str(t.quantity), str(t.fee) if t.fee is not None else ""
    ]

@router.get("/", response_model=TradeListOut)
async def list_trades(page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200),
                      filters: AnalyticsFilters = Depends(filters_query),
                      user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)) -> TradeListOut:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_history_months(user.plan) * 30)
    trades, total = await TradeRepository(session).get_page(user.id, filters, cutoff, page, size)
    return TradeListOut(
        items=[TradeOut.model_validate(t) for t in trades],
        total=total, page=page, size=size,
        pages=ceil(total / size) if total > 0 else 0
    )

@router.get("/symbols", response_model=list[str])
async def list_symbols(user: User = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)) -> list[str]:
    return await TradeRepository(session).user_symbols(user.id)

@router.get("/range", response_model=TradeRangeOut)
async def trades_range(user: User = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)) -> TradeRangeOut:
    first, last = await TradeRepository(session).time_range(user.id)
    return TradeRangeOut(first_trade_at=first, last_trade_at=last)

@router.get("/export")
async def export_trades(filters: AnalyticsFilters = Depends(filters_query),
                        user: User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)):
    repo = TradeRepository(session)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_history_months(user.plan) * 30)

    async def rows():
        async for t in repo.stream_filtered(user.id, filters, cutoff):
            yield _csv_row(t)

    return csv_response("trades.csv", _CSV_HEADER, rows())
