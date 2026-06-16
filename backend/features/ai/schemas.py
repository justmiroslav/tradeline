from datetime import datetime
from typing import Literal

from pydantic import BaseModel

class AiInsightBody(BaseModel):
    verdict: Literal["profitable", "breakeven", "unprofitable"]
    headline: str
    edge: list[str]
    leaks: list[str]
    actions: list[str]

class AiInsightOut(BaseModel):
    insight: AiInsightBody | None
    generated_at: datetime | None
    next_available_at: datetime | None
    can_generate: bool
    cooldown_hours: int
    verified: bool | None = None
    feedback: bool | None = None

class AiFeedbackIn(BaseModel):
    helpful: bool
