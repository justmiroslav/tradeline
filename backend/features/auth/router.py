import asyncio
import uuid

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.api_key import ApiKeyRepository
from db.repositories.email_code import EmailCodeRepository
from db.repositories.refresh_session import RefreshSessionRepository
from db.repositories.user import UserRepository
from domain.config import get_config
from domain.models import User
from features.auth.schemas import GoogleLoginIn, LoginIn, RegisterIn, RegisterResendIn, RegisterVerifyIn, TokenOut, UpdateMeIn, UserOut
from features.auth.service import complete_registration, google_login, resend_registration_code, start_registration
from features.billing.service import cancel_subscription_now
from shared.deps import get_current_user, get_session
from shared.exceptions import UnauthorizedError
from shared.security import create_access_token, create_refresh_token, decode_refresh_token, verify_password
from utils.logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "tl_refresh"

def _access(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(str(user.id), user.token_version))

def _refresh_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=get_config().jwt_refresh_expire_days)

def _set_refresh_cookie(response: Response, user: User, family_id: str, jti: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=create_refresh_token(str(user.id), user.token_version, family_id, jti),
        max_age=get_config().jwt_refresh_expire_days * 24 * 3600,
        httponly=True,
        secure=True,
        samesite="none",
        path="/auth"
    )

def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/auth", secure=True, samesite="none", httponly=True)

async def _start_session(response: Response, session: AsyncSession, user: User) -> None:
    sessions = RefreshSessionRepository(session)
    await sessions.prune_expired(user.id)
    jti = uuid.uuid4().hex
    row = await sessions.create(user.id, jti, _refresh_expiry())
    _set_refresh_cookie(response, user, str(row.family_id), jti)

@router.post("/register", status_code=status.HTTP_202_ACCEPTED)
async def register(body: RegisterIn, request: Request, session: AsyncSession = Depends(get_session)) -> None:
    await start_registration(
        UserRepository(session), EmailCodeRepository(session), request.app.state.email_sender,
        email=body.email, name=body.name.strip(), password=body.password
    )

@router.post("/register/verify", response_model=TokenOut)
async def verify_registration(body: RegisterVerifyIn, response: Response, session: AsyncSession = Depends(get_session)) -> TokenOut:
    user = await complete_registration(
        UserRepository(session), EmailCodeRepository(session), email=body.email, code=body.code
    )
    await _start_session(response, session, user)
    return _access(user)

@router.post("/register/resend", status_code=status.HTTP_204_NO_CONTENT)
async def resend_registration(body: RegisterResendIn, request: Request, session: AsyncSession = Depends(get_session)) -> None:
    await resend_registration_code(
        UserRepository(session), EmailCodeRepository(session), request.app.state.email_sender, email=body.email
    )

@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, response: Response, session: AsyncSession = Depends(get_session)) -> TokenOut:
    user = await UserRepository(session).get_by_email(body.email)
    if not user or not await asyncio.to_thread(verify_password, body.password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")
    if not user.email_verified:
        raise UnauthorizedError("Email not verified — finish the sign-up verification first")

    await _start_session(response, session, user)
    return _access(user)

@router.post("/google", response_model=TokenOut)
async def google(body: GoogleLoginIn, response: Response, session: AsyncSession = Depends(get_session)) -> TokenOut:
    user = await google_login(UserRepository(session), body.credential)
    await _start_session(response, session, user)
    return _access(user)

@router.post("/refresh", response_model=TokenOut)
async def refresh(request: Request, response: Response, session: AsyncSession = Depends(get_session)) -> TokenOut:
    token = request.cookies.get(REFRESH_COOKIE)
    decoded = decode_refresh_token(token) if token else None
    if not decoded:
        raise UnauthorizedError("Invalid refresh token")

    user_id, token_version, family_id, jti = decoded
    user = await UserRepository(session).get_by_id(uuid.UUID(user_id))
    if not user or user.token_version != token_version:
        _clear_refresh_cookie(response)
        raise UnauthorizedError("Refresh token revoked")

    sessions = RefreshSessionRepository(session)
    row = await sessions.get(uuid.UUID(family_id))
    if row is None or row.expires_at <= datetime.now(timezone.utc):
        _clear_refresh_cookie(response)
        raise UnauthorizedError("Session expired — please sign in again")

    if jti == row.jti:
        new_jti = uuid.uuid4().hex
        await sessions.rotate(row, new_jti, _refresh_expiry())
        _set_refresh_cookie(response, user, family_id, new_jti)
    elif jti == row.prev_jti:
        await sessions.touch(row, _refresh_expiry())
        _set_refresh_cookie(response, user, family_id, row.jti)
    else:
        await sessions.delete(uuid.UUID(family_id))
        _clear_refresh_cookie(response)
        logger.warning(f"[auth] refresh reuse detected — session revoked for {user.email}")
        raise UnauthorizedError("Session reuse detected — please sign in again")

    return _access(user)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> None:
    await RefreshSessionRepository(session).delete_for_user(user.id)
    await UserRepository(session).bump_token_version(user)
    _clear_refresh_cookie(response)

@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user, from_attributes=True)

@router.patch("/me", response_model=UserOut)
async def update_me(body: UpdateMeIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> UserOut:
    updated = await UserRepository(session).update_name(user, body.name.strip())
    return UserOut.model_validate(updated, from_attributes=True)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(request: Request, response: Response, user: User = Depends(get_current_user),
                    session: AsyncSession = Depends(get_session)) -> None:
    await cancel_subscription_now(user)

    ws_manager = request.app.state.ws_manager
    ingester = request.app.state.trade_ingester
    keys = await ApiKeyRepository(session).get_all(user.id)

    for key in keys:
        await ws_manager.disconnect(key.id, persist_status=False)
        ingester.forget(key.id)

    await RefreshSessionRepository(session).delete_for_user(user.id)
    await UserRepository(session).delete(user)
    _clear_refresh_cookie(response)
    logger.info(f"[auth] account deleted: {user.email}")
