from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.event import EventRepository
from db.repositories.review import ReviewRepository
from domain.models import Review, User
from features.reviews.schemas import MyReviewOut, ReviewIn, ReviewOut

class ReviewService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def submit(self, user: User, data: ReviewIn) -> Review:
        review = await ReviewRepository(self.session).upsert(user.id, data.rating, data.body)
        await EventRepository(self.session).record("review_submitted", user.id, {"rating": data.rating})
        return review

    async def public(self) -> list[ReviewOut]:
        rows = await ReviewRepository(self.session).approved()
        return [ReviewOut(id=r.id, name=r.user.name, rating=r.rating, body=r.body, created_at=r.created_at) for r in rows]

    async def mine(self, user: User) -> MyReviewOut | None:
        review = await ReviewRepository(self.session).get_for_user(user.id)
        return MyReviewOut(rating=review.rating, body=review.body, status=review.status) if review else None
