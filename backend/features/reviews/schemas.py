from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str = Field(min_length=10, max_length=500)

class ReviewOut(BaseModel):
    id: UUID
    name: str
    rating: int
    body: str
    created_at: datetime

class MyReviewOut(BaseModel):
    rating: int
    body: str
    status: str
