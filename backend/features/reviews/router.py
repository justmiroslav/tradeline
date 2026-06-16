import html

from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models import User
from features.reviews.schemas import MyReviewOut, ReviewIn, ReviewOut
from features.reviews.service import ReviewService
from shared.deps import get_current_user, get_session

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.get("/", response_model=list[ReviewOut])
async def list_reviews(session: AsyncSession = Depends(get_session)) -> list[ReviewOut]:
    return await ReviewService(session).public()

@router.get("/me", response_model=Optional[MyReviewOut])
async def my_review(user: User = Depends(get_current_user),
                    session: AsyncSession = Depends(get_session)) -> Optional[MyReviewOut]:
    return await ReviewService(session).mine(user)

@router.post("/", response_model=MyReviewOut)
async def submit_review(body: ReviewIn, request: Request, user: User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)) -> MyReviewOut:
    review = await ReviewService(session).submit(user, body)
    telegram = getattr(request.app.state, "telegram", None)
    if telegram is not None:
        await telegram.notify_review(
            f"\U0001F514 <b>New review pending</b>\n"
            f"from {html.escape(user.email)}\n"
            f"{review.rating}★ — {html.escape(review.body)}"
        )
    return MyReviewOut(rating=review.rating, body=review.body, status=review.status)
