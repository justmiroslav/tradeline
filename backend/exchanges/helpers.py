import random, base64, hmac, hashlib, aiohttp

from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode, urlparse

from domain.enums import TradeSide
from shared.exceptions import (
    ExchangeUnavailableError, InvalidCredentialsError, IpNotWhitelistedError,
    KeyAccessRestrictedError, RateLimitError
)

from .types import Kline

FETCH_ERRORS = (aiohttp.ClientError, aiohttp.ContentTypeError, KeyError, ValueError, TypeError)

PROBE_FATAL_TYPES = (
    InvalidCredentialsError, IpNotWhitelistedError, KeyAccessRestrictedError,
    RateLimitError, ExchangeUnavailableError
)

def dec(val):
    if val is None or val == "":
        raise ValueError("required Decimal field is None/empty")
    return Decimal(str(val))

def dec_opt(val):
    if val is None or val == "":
        return None
    return Decimal(str(val))

def from_ms(ms):
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)

def qs(params):
    if not params:
        return ""
    return urlencode([(k, v) for k, v in params.items() if v != "" and v is not None])

def build_url(base: str, path: str, query: str = "") -> str:
    return f"{base}{path}?{query}" if query else f"{base}{path}"

def sign_b64(secret: str, message: str) -> str:
    return base64.b64encode(hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()).decode()

def to_side(raw: str) -> TradeSide:
    return TradeSide.BUY if raw.lower() == "buy" else TradeSide.SELL

def abs_or_none(value):
    return abs(value) if value is not None else None

def expo_jitter(attempt, base=0.3, cap=30.0, floor=0.0):
    return max(floor, random.uniform(0, min(cap, base * (2 ** max(attempt, 0)))))

def proxy_label(proxy: str | None) -> str | None:
    return urlparse(proxy).hostname if proxy else None

def klines_from_rows(rows, newest_first=False) -> list[Kline]:
    data = reversed(rows) if newest_first else rows
    return [
        Kline(time_ms=int(r[0]), open=dec(r[1]), high=dec(r[2]), low=dec(r[3]), close=dec(r[4]), volume=dec(r[5]))
        for r in data
    ]
