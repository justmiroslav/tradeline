import uuid

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select

from db.repositories.base import BaseRepository
from domain.models import RefreshSession

class RefreshSessionRepository(BaseRepository):
    async def create(self, user_id: uuid.UUID, jti: str, expires_at: datetime) -> RefreshSession:
        session = RefreshSession(user_id=user_id, jti=jti, expires_at=expires_at)
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get(self, family_id: uuid.UUID) -> Optional[RefreshSession]:
        return await self._one(select(RefreshSession).where(RefreshSession.family_id == family_id))

    async def rotate(self, session: RefreshSession, jti: str, expires_at: datetime) -> None:
        session.prev_jti = session.jti
        session.jti = jti
        session.expires_at = expires_at
        await self.session.commit()

    async def touch(self, session: RefreshSession, expires_at: datetime) -> None:
        session.expires_at = expires_at
        await self.session.commit()

    async def delete(self, family_id: uuid.UUID) -> None:
        await self.session.execute(delete(RefreshSession).where(RefreshSession.family_id == family_id))
        await self.session.commit()

    async def delete_for_user(self, user_id: uuid.UUID) -> None:
        await self.session.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
        await self.session.commit()

    async def prune_expired(self, user_id: uuid.UUID) -> None:
        await self.session.execute(delete(RefreshSession).where(
            RefreshSession.user_id == user_id,
            RefreshSession.expires_at < datetime.now(timezone.utc)
        ))
        await self.session.commit()
