from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.positions import PositionsRepository
from domain.enums import PositionStatus
from domain.filters import AnalyticsFilters
from domain.models import Position, User
from features.analytics.deps import filters_query
from features.positions.schemas import PositionListOut, PositionOut
from shared.csv import csv_response
from shared.deps import get_current_user, get_session

router = APIRouter(prefix="/positions", tags=["positions"])

_CSV_HEADER = ["opened_at", "closed_at", "exchange", "market_type", "symbol", "side", "status",
               "size", "entry_price", "exit_price", "entry_notional", "net_pnl", "fees", "setup", "trade_count"]

def _csv_row(p: Position) -> list:
    size = p.entry_notional / p.entry_price if p.entry_price else 0
    return [
        p.opened_at.isoformat(), p.closed_at.isoformat() if p.closed_at else "",
        p.exchange.value, p.market_type.value, p.symbol, p.side.value, p.status.value,
        str(size), str(p.entry_price), str(p.exit_price) if p.exit_price is not None else "",
        str(p.entry_notional), str(p.realized_pnl - p.fees_quote), str(p.fees_quote), p.setup or "", p.trade_count
    ]

@router.get("/", response_model=PositionListOut)
async def list_positions(page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200),
                         status: PositionStatus | None = Query(None),
                         filters: AnalyticsFilters = Depends(filters_query),
                         user: User = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session)) -> PositionListOut:
    rows, total = await PositionsRepository(session).list_page(user.id, filters, status, page, size)
    return PositionListOut(
        items=[PositionOut.model_validate(p) for p in rows], total=total, page=page, size=size,
        pages=ceil(total / size) if total > 0 else 0
    )

@router.get("/export")
async def export_positions(status: PositionStatus | None = Query(None),
                           filters: AnalyticsFilters = Depends(filters_query),
                           user: User = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session)):
    repo = PositionsRepository(session)

    async def rows():
        async for p in repo.stream_all(user.id, filters, status):
            yield _csv_row(p)

    return csv_response("positions.csv", _CSV_HEADER, rows())
