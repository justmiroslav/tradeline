import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import delete, or_, select, update

from db.repositories.base import BaseRepository
from domain.enums import PlanTier
from domain.models import User

_UNSET = object()

class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self._one(select(User).where(User.id == user_id))

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self._one(select(User).where(User.email == email))

    async def get_by_stripe_customer_id(self, customer_id: str) -> Optional[User]:
        return await self._one(select(User).where(User.stripe_customer_id == customer_id))

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        return await self._one(select(User).where(User.google_id == google_id))

    async def email_taken(self, email: str) -> bool:
        return await self._one(select(User).where(User.email == email)) is not None

    async def create(self, email: str, name: str, password_hash: str, *,
                     google_id: str | None = None, avatar_url: str | None = None, email_verified: bool = False) -> User:
        user = User(email=email, name=name, password_hash=password_hash,
                    google_id=google_id, avatar_url=avatar_url, email_verified=email_verified)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_google(self, user: User, google_id: str, avatar_url: str | None) -> None:
        user.google_id = google_id
        if avatar_url:
            user.avatar_url = avatar_url
        await self.session.commit()

    async def update_name(self, user: User, name: str) -> User:
        user.name = name
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def replace_unverified(self, user: User, name: str, password_hash: str) -> User:
        user.name = name
        user.password_hash = password_hash
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.execute(delete(User).where(User.id == user.id))
        await self.session.commit()

    async def set_email_verified(self, user: User) -> None:
        user.email_verified = True
        await self.session.commit()

    async def bump_token_version(self, user: User) -> None:
        user.token_version += 1
        await self.session.commit()

    async def set_plan(self, user: User, tier: PlanTier) -> None:
        user.plan = tier
        await self.session.commit()

    async def set_billing(self, user: User, *, customer_id=_UNSET, subscription_id=_UNSET,
                          status=_UNSET, current_period_end=_UNSET, cancel_at_period_end=_UNSET) -> None:
        if customer_id is not _UNSET:
            user.stripe_customer_id = customer_id
        if subscription_id is not _UNSET:
            user.stripe_subscription_id = subscription_id
        if status is not _UNSET:
            user.subscription_status = status
        if current_period_end is not _UNSET:
            user.current_period_end = current_period_end
        if cancel_at_period_end is not _UNSET:
            user.cancel_at_period_end = cancel_at_period_end
        await self.session.commit()

    async def set_ai_insight(self, user: User, text: str, at: datetime, verified: bool) -> None:
        user.last_ai_insight = text
        user.last_ai_insight_at = at
        user.last_ai_verified = verified
        user.last_ai_feedback = None
        await self.session.commit()

    async def set_ai_feedback(self, user: User, helpful: bool) -> None:
        user.last_ai_feedback = helpful
        await self.session.commit()

    async def claim_ai_slot(self, user_id: uuid.UUID, at: datetime, cutoff: datetime) -> bool:
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .where(or_(User.last_ai_insight_at.is_(None), User.last_ai_insight_at <= cutoff))
            .values(last_ai_insight_at=at)
        )
        await self.session.commit()
        return result.rowcount == 1

    async def reset_ai_slot(self, user_id: uuid.UUID, prev_at: Optional[datetime]) -> None:
        await self.session.execute(update(User).where(User.id == user_id).values(last_ai_insight_at=prev_at))
        await self.session.commit()
