import uuid

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select

from db.repositories.base import BaseRepository
from domain.models import Event

class EventRepository(BaseRepository):
    async def record(self, event_type: str, user_id: Optional[uuid.UUID], payload: dict) -> None:
        self.session.add(Event(type=event_type, user_id=user_id, payload=payload))
        await self.session.commit()

    async def by_type(self, event_type: str, since: Optional[datetime] = None) -> list[Event]:
        stmt = select(Event).where(Event.type == event_type)
        if since is not None:
            stmt = stmt.where(Event.created_at >= since)
        return await self._all(stmt)

    async def counts(self, since: Optional[datetime] = None) -> dict[str, int]:
        stmt = select(Event.type, func.count()).group_by(Event.type)
        if since is not None:
            stmt = stmt.where(Event.created_at >= since)
        return {row[0]: row[1] for row in (await self.session.execute(stmt)).all()}

    async def distinct_user_counts(self) -> dict[str, int]:
        stmt = (
            select(Event.type, func.count(func.distinct(Event.user_id)))
            .where(Event.user_id.is_not(None))
            .group_by(Event.type)
        )
        return {row[0]: row[1] for row in (await self.session.execute(stmt)).all()}
