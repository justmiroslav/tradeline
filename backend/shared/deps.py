import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import SessionFactory
from db.repositories.user import UserRepository
from domain.models import User
from shared.security import decode_token

_bearer = HTTPBearer()

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionFactory() as session:
        yield session

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer), session: AsyncSession = Depends(get_session)) -> User:
    decoded = decode_token(creds.credentials)
    if not decoded:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id, token_ver = decoded

    user = await UserRepository(session).get_by_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.token_version != token_ver:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    return user
