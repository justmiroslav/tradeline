import uuid

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.repositories.base import BaseRepository
from domain.models import Review

class ReviewRepository(BaseRepository):
    async def get_for_user(self, user_id: uuid.UUID) -> Optional[Review]:
        return await self._one(select(Review).where(Review.user_id == user_id))

    async def get(self, review_id: uuid.UUID) -> Optional[Review]:
        return await self._one(select(Review).where(Review.id == review_id))

    async def upsert(self, user_id: uuid.UUID, rating: int, body: str) -> Review:
        review = await self.get_for_user(user_id)
        if review is None:
            review = Review(user_id=user_id, rating=rating, body=body, status="pending")
            self.session.add(review)
        else:
            review.rating = rating
            review.body = body
            review.status = "pending"
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def set_status(self, review: Review, status: str) -> None:
        review.status = status
        await self.session.commit()

    async def approved(self, limit: int = 12) -> list[Review]:
        return await self._all(
            select(Review).options(selectinload(Review.user))
            .where(Review.status == "approved").order_by(Review.created_at.desc()).limit(limit)
        )

    async def by_status(self, status: str, limit: int = 20) -> list[Review]:
        return await self._all(
            select(Review).options(selectinload(Review.user))
            .where(Review.status == status).order_by(Review.created_at.desc()).limit(limit)
        )
