from asyncio import to_thread
from typing import Optional

import aiohttp

from db.repositories.email_code import EmailCodeRepository
from db.repositories.event import EventRepository
from db.repositories.user import UserRepository
from domain.config import get_config
from domain.models import User
from features.email.sender import EmailSender
from features.email.service import confirm_verification, request_verification
from shared.exceptions import BadRequestError, ConflictError, UnauthorizedError
from shared.security import hash_password
from utils.logger import brief, logger

_OAUTH_PASSWORD = "google-oauth"
_GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")

async def _verify_google(credential: str, client_id: str) -> Optional[dict]:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as http:
            async with http.get(_GOOGLE_TOKENINFO_URL, params={"id_token": credential}) as resp:
                if resp.status != 200:
                    logger.warning(f"[auth] google tokeninfo {resp.status}: {(await resp.text())[:200]}")
                    return None
                claims = await resp.json()
    except (aiohttp.ClientError, TimeoutError) as e:
        logger.warning(f"[auth] google tokeninfo request failed: {brief(e)}")
        return None
    if claims.get("aud") != client_id:
        logger.warning(f"[auth] google token audience mismatch: {claims.get('aud')}")
        return None
    if claims.get("iss") not in _GOOGLE_ISSUERS:
        logger.warning(f"[auth] google token issuer mismatch: {claims.get('iss')}")
        return None
    return claims

async def google_login(users: UserRepository, credential: str) -> User:
    cfg = get_config()
    if not cfg.google_client_id:
        raise BadRequestError("Google sign-in is not configured")
    info = await _verify_google(credential, cfg.google_client_id)
    if info is None:
        raise UnauthorizedError("Could not verify your Google sign-in — try again")

    google_id = info.get("sub")
    email = info.get("email")
    verified = info.get("email_verified")
    if isinstance(verified, str):
        verified = verified.lower() == "true"
    if not google_id or not email or not verified:
        raise UnauthorizedError("Google account is missing a verified email")

    name = (info.get("name") or email.split("@")[0]).strip()[:64] or email[:64]
    avatar = info.get("picture")

    user = await users.get_by_google_id(google_id)
    if user is not None:
        if avatar and user.avatar_url != avatar:
            await users.set_google(user, google_id, avatar)
        logger.info(f"[auth] google login: {email}")
        return user

    existing = await users.get_by_email(email)
    if existing is not None:
        await users.set_google(existing, google_id, avatar)
        logger.info(f"[auth] google linked to existing account: {email}")
        return existing

    user = await users.create(email, name, _OAUTH_PASSWORD, google_id=google_id, avatar_url=avatar, email_verified=True)
    await EventRepository(users.session).record("signup", user.id, {"method": "google"})
    logger.info(f"[auth] google signup: {email}")
    return user

async def start_registration(users: UserRepository, codes: EmailCodeRepository, sender: EmailSender,
                             *, email: str, name: str, password: str) -> None:
    existing = await users.get_by_email(email)
    if existing is not None and existing.email_verified:
        raise ConflictError("Email already registered")

    password_hash = await to_thread(hash_password, password)
    if existing is None:
        user = await users.create(email, name, password_hash)
    else:
        user = await users.replace_unverified(existing, name, password_hash)

    await request_verification(codes, sender, user)
    logger.info(f"[auth] registration started: {email}")

async def complete_registration(users: UserRepository, codes: EmailCodeRepository, *, email: str, code: str) -> User:
    user = await users.get_by_email(email)
    if user is None or user.email_verified:
        raise UnauthorizedError("No pending sign-up for this email — start registration first")

    await confirm_verification(codes, users, user, code)
    await EventRepository(users.session).record("signup", user.id, {"method": "email"})
    logger.info(f"[auth] user registered: {user.email}")
    return user

async def resend_registration_code(users: UserRepository, codes: EmailCodeRepository, sender: EmailSender, *, email: str) -> None:
    user = await users.get_by_email(email)
    if user is None or user.email_verified:
        raise UnauthorizedError("No pending sign-up for this email — start registration first")

    await request_verification(codes, sender, user)
