import asyncio, hashlib, hmac, secrets

from datetime import datetime, timedelta, timezone

from db.repositories.email_code import EmailCodeRepository
from db.repositories.user import UserRepository
from domain.models import User
from features.email.sender import EmailSender
from shared.exceptions import InvalidCodeError, TooManyRequestsError
from utils.logger import brief, logger

_deliveries: set = set()

VERIFY_EMAIL = "verify_email"
CODE_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_SENDS_PER_HOUR = 5
MAX_ATTEMPTS = 5

def generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

def _subject() -> str:
    return "Confirm your Tradeline account"

def _body(code: str) -> str:
    return f"Your Tradeline verification code: {code}\n\nThe code expires in 10 minutes"

def _html(code: str) -> str:
    return f"<p>Your Tradeline verification code: <strong>{code}</strong></p><p>The code expires in 10 minutes</p>"

async def request_verification(codes: EmailCodeRepository, sender: EmailSender, user: User) -> None:
    if user.email_verified:
        raise InvalidCodeError("Email is already verified")

    now = datetime.now(timezone.utc)
    if await codes.count_recent(user.id, VERIFY_EMAIL, now - timedelta(hours=1)) >= MAX_SENDS_PER_HOUR:
        raise TooManyRequestsError("Too many codes requested — try again in an hour")
    last = await codes.latest_active(user.id, VERIFY_EMAIL)
    if last is not None and now - last.created_at < RESEND_COOLDOWN:
        raise TooManyRequestsError("Code already sent — wait a minute before requesting a new one")

    code = generate_code()
    await codes.create(user.id, VERIFY_EMAIL, hash_code(code), now + CODE_TTL)
    task = asyncio.create_task(_deliver(sender, user.email, _subject(), _body(code), _html(code)))
    _deliveries.add(task)
    task.add_done_callback(_deliveries.discard)

async def _deliver(sender: EmailSender, email: str, subject: str, body: str, html: str) -> None:
    try:
        await sender.send(email, subject, body, html)
        logger.info(f"[email] verification code sent to {email}")
    except Exception as e:
        logger.warning(f"[email] failed to send verification code to {email}: {brief(e)}")

async def flush_deliveries() -> None:
    if _deliveries:
        await asyncio.gather(*list(_deliveries), return_exceptions=True)

async def confirm_verification(codes: EmailCodeRepository, users: UserRepository, user: User, code: str) -> None:
    active = await codes.latest_active(user.id, VERIFY_EMAIL)
    if active is None:
        raise InvalidCodeError("Invalid or expired code")
    if active.attempts >= MAX_ATTEMPTS:
        raise InvalidCodeError("Too many attempts — request a new code")

    await codes.record_attempt(active)
    if not hmac.compare_digest(active.code_hash, hash_code(code)):
        raise InvalidCodeError("Invalid or expired code")

    await codes.consume(active)
    await users.set_email_verified(user)
    logger.info(f"[email] {user.email} verified")
