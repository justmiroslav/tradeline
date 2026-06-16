from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, field_serializer

from domain.enums import Exchange, MarketType

SUSPENDED_BY_PLAN = "Suspended by the plan limit — upgrade to Pro to reconnect this key"

class ApiKeyIn(BaseModel):
    exchange: Exchange
    api_key: str = Field(min_length=1, max_length=256)
    api_secret: str = Field(min_length=1, max_length=256)
    passphrase: Optional[str] = Field(default=None, max_length=256)
    label: Optional[str] = Field(default=None, max_length=64)
    markets: list[MarketType] = []

class ApiKeyUpdate(BaseModel):
    label: str = Field(min_length=1, max_length=64)

class ApiKeyOut(BaseModel):
    id: UUID
    exchange: Exchange
    label: Optional[str]
    capabilities: list[str]
    account_uid: Optional[str]
    ip_restricted: bool
    ws_connected: bool
    last_error: Optional[str]
    last_error_at: Optional[datetime]
    created_at: datetime

    @computed_field
    @property
    def suspended(self) -> bool:
        return self.last_error == SUSPENDED_BY_PLAN

    @field_serializer("created_at", "last_error_at")
    def _as_utc(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

class ApiKeyValidationResult(BaseModel):
    id: UUID
    exchange: Exchange
    capabilities: list[str]
    ip_restricted: bool
    replaced: bool
    message: str
