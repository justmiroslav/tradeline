import uuid
from datetime import datetime
from typing import AsyncIterator, Optional, Sequence

from sqlalchemy import select, func, and_, delete, update

from db.repositories.base import BaseRepository
from db.repositories.filtering import apply_filters
from domain.enums import Exchange, MarketType, PositionSide, PositionStatus
from domain.filters import AnalyticsFilters
from domain.models import Position

class PositionsRepository(BaseRepository):
    async def find_open(self, user_id: uuid.UUID, api_key_id: uuid.UUID, exchange: Exchange, market_type: MarketType, symbol: str, side: PositionSide) -> Optional[Position]:
        r = await self.session.execute(
            select(Position).where(
                and_(
                    Position.user_id == user_id,
                    Position.api_key_id == api_key_id,
                    Position.exchange == exchange,
                    Position.market_type == market_type,
                    Position.symbol == symbol,
                    Position.side == side,
                    Position.status == PositionStatus.OPEN
                )
            )
        )
        return r.scalar_one_or_none()

    async def get(self, position_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Position]:
        r = await self.session.execute(
            select(Position).where(and_(Position.id == position_id, Position.user_id == user_id))
        )
        return r.scalar_one_or_none()

    def _filtered(self, user_id: uuid.UUID, filters: AnalyticsFilters, status: Optional[PositionStatus]):
        base = select(Position).where(Position.user_id == user_id)
        base = apply_filters(base, Position, filters, Position.closed_at, Position.setup, Position.side)
        if status is not None:
            base = base.where(Position.status == status)
        return base

    async def list_page(self, user_id: uuid.UUID, filters: AnalyticsFilters, status: Optional[PositionStatus] = None, page: int = 1, size: int = 50) -> tuple[Sequence[Position], int]:
        base = self._filtered(user_id, filters, status)
        total = (await self.session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        rows = (await self.session.execute(
            base.order_by(Position.opened_at.desc(), Position.id.desc()).offset((page - 1) * size).limit(size)
        )).scalars().all()
        return rows, total

    async def stream_all(self, user_id: uuid.UUID, filters: AnalyticsFilters, status: Optional[PositionStatus] = None) -> AsyncIterator[Position]:
        stmt = self._filtered(user_id, filters, status).order_by(Position.opened_at.desc(), Position.id.desc())
        result = await self.session.stream_scalars(stmt.execution_options(yield_per=500))
        async for position in result:
            yield position

    async def needing_excursions(self, limit: int, since: datetime) -> Sequence[Position]:
        r = await self.session.execute(
            select(Position).where(and_(
                Position.status == PositionStatus.CLOSED, Position.closed_at.is_not(None),
                Position.closed_at >= since, Position.mfe.is_(None)
            )).limit(limit)
        )
        return r.scalars().all()

    async def set_excursions(self, position_id: uuid.UUID, mfe, mae) -> None:
        await self.session.execute(update(Position).where(Position.id == position_id).values(mfe=mfe, mae=mae))

    async def reassign_key(self, old_api_key_id: uuid.UUID, new_api_key_id: uuid.UUID, markets: list[MarketType]) -> None:
        if not markets:
            return
        await self.session.execute(
            update(Position)
            .where(and_(Position.api_key_id == old_api_key_id, Position.market_type.in_(markets)))
            .values(api_key_id=new_api_key_id)
        )

    async def open_spot_for_key(self, api_key_id: uuid.UUID) -> Sequence[Position]:
        r = await self.session.execute(
            select(Position).where(and_(
                Position.api_key_id == api_key_id,
                Position.market_type == MarketType.SPOT,
                Position.status == PositionStatus.OPEN
            ))
        )
        return r.scalars().all()

    def add(self, position: Position) -> None:
        self.session.add(position)

    async def flush(self) -> None:
        await self.session.flush()

    async def delete_for_user(self, user_id: uuid.UUID) -> None:
        await self.session.execute(delete(Position).where(Position.user_id == user_id))
