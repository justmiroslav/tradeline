import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_, update

from db.repositories.base import BaseRepository
from domain.models import EmailCode

class EmailCodeRepository(BaseRepository):
    async def create(self, user_id: uuid.UUID, purpose: str, code_hash: str, expires_at: datetime) -> EmailCode:
        await self.session.execute(
            update(EmailCode)
            .where(and_(EmailCode.user_id == user_id, EmailCode.purpose == purpose, EmailCode.consumed_at.is_(None)))
            .values(consumed_at=datetime.now(timezone.utc))
        )
        code = EmailCode(user_id=user_id, purpose=purpose, code_hash=code_hash, expires_at=expires_at)
        self.session.add(code)
        await self.session.commit()
        await self.session.refresh(code)
        return code

    async def latest_active(self, user_id: uuid.UUID, purpose: str) -> Optional[EmailCode]:
        r = await self.session.execute(
            select(EmailCode).where(and_(
                EmailCode.user_id == user_id,
                EmailCode.purpose == purpose,
                EmailCode.consumed_at.is_(None),
                EmailCode.expires_at > datetime.now(timezone.utc)
            )).order_by(EmailCode.created_at.desc()).limit(1)
        )
        return r.scalar_one_or_none()

    async def count_recent(self, user_id: uuid.UUID, purpose: str, since: datetime) -> int:
        r = await self.session.execute(
            select(func.count()).select_from(EmailCode).where(and_(
                EmailCode.user_id == user_id, EmailCode.purpose == purpose, EmailCode.created_at >= since
            ))
        )
        return r.scalar_one()

    async def record_attempt(self, code: EmailCode) -> None:
        code.attempts += 1
        await self.session.commit()

    async def consume(self, code: EmailCode) -> None:
        code.consumed_at = datetime.now(timezone.utc)
        await self.session.commit()
