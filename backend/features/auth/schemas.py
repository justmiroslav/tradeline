from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from domain.enums import PlanTier

class RegisterIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8)

class RegisterVerifyIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

class RegisterResendIn(BaseModel):
    email: EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class GoogleLoginIn(BaseModel):
    credential: str = Field(min_length=1, max_length=4096)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: UUID
    email: str
    name: str
    plan: PlanTier
    email_verified: bool
    avatar_url: str | None = None

class UpdateMeIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
