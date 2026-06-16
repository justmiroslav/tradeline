import jwt, bcrypt, hashlib, uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet

from domain.config import get_config

def _fernet() -> Fernet:
    return Fernet(get_config().fernet_key.encode())

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode()[:72], bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode()[:72], hashed.encode())
    except ValueError:
        return False

def _encode_token(user_id: str, token_version: int, token_type: str, lifetime: timedelta) -> str:
    exp = datetime.now(timezone.utc) + lifetime
    return jwt.encode(
        {"sub": user_id, "ver": token_version, "typ": token_type, "exp": exp},
        get_config().jwt_secret,
        algorithm="HS256"
    )

def create_access_token(user_id: str, token_version: int) -> str:
    return _encode_token(user_id, token_version, "access", timedelta(minutes=get_config().jwt_expire_minutes))

def create_refresh_token(user_id: str, token_version: int, family_id: str, jti: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=get_config().jwt_refresh_expire_days)
    return jwt.encode(
        {"sub": user_id, "ver": token_version, "typ": "refresh", "fam": family_id, "jti": jti, "exp": exp},
        get_config().jwt_secret,
        algorithm="HS256"
    )

def decode_token(token: str, expected_type: str = "access") -> Optional[tuple[str, int]]:
    try:
        payload = jwt.decode(token, get_config().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    ver = payload.get("ver")
    if not isinstance(sub, str) or not isinstance(ver, int) or payload.get("typ") != expected_type:
        return None
    try:
        uuid.UUID(sub)
    except ValueError:
        return None
    return sub, ver

def decode_refresh_token(token: str) -> Optional[tuple[str, int, str, str]]:
    try:
        payload = jwt.decode(token, get_config().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    sub, ver, fam, jti = payload.get("sub"), payload.get("ver"), payload.get("fam"), payload.get("jti")
    if not (isinstance(sub, str) and isinstance(ver, int) and isinstance(fam, str) and isinstance(jti, str)):
        return None
    if payload.get("typ") != "refresh":
        return None
    try:
        uuid.UUID(sub)
        uuid.UUID(fam)
    except ValueError:
        return None
    return sub, ver, fam, jti

def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()
