import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import func, select

from db.repositories.base import BaseRepository
from db.repositories.filtering import apply_filters
from domain.enums import PositionStatus
from domain.filters import AnalyticsFilters
from domain.models import Position

class AnalyticsRepository(BaseRepository):
    def _closed(self, user_id: uuid.UUID, filters: AnalyticsFilters):
        stmt = select(Position).where(
            Position.user_id == user_id,
            Position.status == PositionStatus.CLOSED,
            Position.closed_at.is_not(None)
        )
        return apply_filters(stmt, Position, filters, Position.closed_at, Position.setup, Position.side)

    async def closed_positions(self, user_id: uuid.UUID, filters: AnalyticsFilters) -> Sequence[Position]:
        r = await self.session.execute(self._closed(user_id, filters).order_by(Position.closed_at, Position.id))
        return r.scalars().all()

    async def closed_positions_since(self, user_id: uuid.UUID, filters: AnalyticsFilters, since: datetime) -> Sequence[Position]:
        stmt = self._closed(user_id, filters).where(Position.closed_at >= since)
        r = await self.session.execute(stmt.order_by(Position.closed_at, Position.id))
        return r.scalars().all()

    async def open_positions(self, user_id: uuid.UUID, filters: AnalyticsFilters) -> Sequence[Position]:
        stmt = select(Position).where(Position.user_id == user_id, Position.status == PositionStatus.OPEN)
        stmt = apply_filters(stmt, Position, filters, None, Position.setup, Position.side)
        r = await self.session.execute(stmt)
        return r.scalars().all()

    async def count_incomplete(self, user_id: uuid.UUID) -> int:
        r = await self.session.execute(
            select(func.count()).select_from(Position).where(
                Position.user_id == user_id, Position.status == PositionStatus.INCOMPLETE
            )
        )
        return r.scalar_one()
