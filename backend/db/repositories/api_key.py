import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy import select, and_, func, update, delete

from db.repositories.base import BaseRepository
from domain.enums import Exchange
from domain.models import ApiKey

_FIRST_CHECK_WINDOW_SECONDS = 600

def initial_next_check() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=random.uniform(0, _FIRST_CHECK_WINDOW_SECONDS))

class ApiKeyRepository(BaseRepository):
    async def get_all(self, user_id: uuid.UUID) -> Sequence[ApiKey]:
        r = await self.session.execute(
            select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at, ApiKey.id)
        )
        return r.scalars().all()

    async def get_all_global(self) -> Sequence[ApiKey]:
        r = await self.session.execute(select(ApiKey))
        return r.scalars().all()

    async def get_by_id(self, key_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ApiKey]:
        r = await self.session.execute(
            select(ApiKey).where(and_(ApiKey.id == key_id, ApiKey.user_id == user_id))
        )
        return r.scalar_one_or_none()

    async def get_global(self, key_id: uuid.UUID) -> Optional[ApiKey]:
        r = await self.session.execute(select(ApiKey).where(ApiKey.id == key_id))
        return r.scalar_one_or_none()

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        r = await self.session.execute(
            select(func.count()).select_from(ApiKey).where(ApiKey.user_id == user_id)
        )
        return r.scalar_one()

    async def count_by_exchange(self, user_id: uuid.UUID, exchange: Exchange) -> int:
        r = await self.session.execute(
            select(func.count()).select_from(ApiKey).where(
                and_(ApiKey.user_id == user_id, ApiKey.exchange == exchange)
            )
        )
        return r.scalar_one()

    async def exists_by_hash(self, user_id: uuid.UUID, key_hash: str) -> bool:
        r = await self.session.execute(
            select(ApiKey).where(and_(ApiKey.user_id == user_id, ApiKey.api_key_hash == key_hash))
        )
        return r.scalar_one_or_none() is not None

    async def find_all_by_account(self, user_id: uuid.UUID, exchange: Exchange, account_uid: str) -> Sequence[ApiKey]:
        r = await self.session.execute(
            select(ApiKey).where(and_(
                ApiKey.user_id == user_id, ApiKey.exchange == exchange, ApiKey.account_uid == account_uid
            ))
        )
        return r.scalars().all()

    def add(self, *, user_id: uuid.UUID, exchange: Exchange,
            api_key_encrypted: str, api_secret_encrypted: str,
            api_key_hash: str, passphrase_encrypted: Optional[str],
            label: Optional[str], capabilities: list[str],
            account_uid: Optional[str], ip_restricted: bool) -> ApiKey:
        key = ApiKey(
            user_id=user_id, exchange=exchange,
            api_key_encrypted=api_key_encrypted,
            api_secret_encrypted=api_secret_encrypted,
            api_key_hash=api_key_hash, passphrase_encrypted=passphrase_encrypted,
            label=label, capabilities=capabilities, account_uid=account_uid,
            ip_restricted=ip_restricted, next_check_at=initial_next_check()
        )
        self.session.add(key)
        return key

    async def update_label(self, key: ApiKey, label: str) -> None:
        key.label = label
        await self.session.commit()

    async def update_capabilities(self, key_id: uuid.UUID, capabilities: list[str]) -> None:
        await self.session.execute(
            update(ApiKey).where(ApiKey.id == key_id).values(capabilities=capabilities)
        )
        await self.session.commit()

    async def update_ws_status(self, key_id: uuid.UUID, connected: bool) -> None:
        await self.session.execute(
            update(ApiKey).where(ApiKey.id == key_id).values(ws_connected=connected)
        )
        await self.session.commit()

    async def due_for_check(self, limit: int) -> Sequence[ApiKey]:
        r = await self.session.execute(
            select(ApiKey)
            .where(ApiKey.next_check_at <= datetime.now(timezone.utc))
            .order_by(ApiKey.next_check_at)
            .limit(limit)
        )
        return r.scalars().all()

    async def set_next_check(self, key_id: uuid.UUID, when: datetime) -> None:
        await self.session.execute(
            update(ApiKey).where(ApiKey.id == key_id).values(next_check_at=when)
        )
        await self.session.commit()

    async def mark_checked(self, key_id: uuid.UUID, next_check_at: datetime, last_error: Optional[str],
                           ip_restricted: Optional[bool] = None, account_uid: Optional[str] = None) -> None:
        values: dict = {
            "next_check_at": next_check_at,
            "last_error": last_error,
            "last_error_at": datetime.now(timezone.utc) if last_error else None
        }
        if ip_restricted is not None:
            values["ip_restricted"] = ip_restricted
        if account_uid is not None:
            values["account_uid"] = account_uid
        await self.session.execute(update(ApiKey).where(ApiKey.id == key_id).values(**values))
        await self.session.commit()

    async def set_last_error(self, key_id: uuid.UUID, message: str) -> None:
        await self.session.execute(
            update(ApiKey).where(ApiKey.id == key_id).values(
                last_error=message,
                last_error_at=datetime.now(timezone.utc)
            )
        )
        await self.session.commit()

    async def remove(self, key: ApiKey) -> None:
        await self.session.execute(delete(ApiKey).where(ApiKey.id == key.id))

    async def delete(self, key: ApiKey) -> None:
        await self.remove(key)
        await self.session.commit()
