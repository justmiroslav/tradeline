from domain.config import get_config
from shared.exceptions import (
    ExchangeError, ExchangeUnavailableError, InvalidCredentialsError,
    IpNotWhitelistedError, KeyAccessRestrictedError, RateLimitError
)
from utils.logger import logger

WS_AUTH_FATAL = (InvalidCredentialsError, KeyAccessRestrictedError, IpNotWhitelistedError)

class WSAuthFatalError(ConnectionError):
    pass

def friendly_message(kls, name: str) -> str | None:
    if kls is IpNotWhitelistedError:
        return (f"{name} rejected our IP — add {get_config().whitelist_hint} to this key's "
                f"IP whitelist on {name}, then press Re-check")
    if kls is InvalidCredentialsError:
        return f"{name} did not accept the API key or secret — re-paste them or create a new key"
    if kls is RateLimitError:
        return f"{name} is rate-limiting requests right now — it recovers on its own, try again in a minute"
    if kls is ExchangeUnavailableError:
        return f"{name} is temporarily unavailable — try again in a few minutes"
    return None

class ExchangeErrors:
    _NAME = ""
    _CODES = {}
    _PASSPHRASE_CODES = ()

    @classmethod
    def parse(cls, code, msg):
        key = cls._normalize(code)
        kls = cls._CODES.get(key)
        if kls is None:
            logger.info(f"[{cls._NAME}] unmapped error code {code}: {msg}")
            return ExchangeError(f"{cls._NAME}: {msg}")
        if key in cls._PASSPHRASE_CODES:
            return kls(f"{cls._NAME}: the passphrase is incorrect — it is the phrase you set when creating the key")
        friendly = friendly_message(kls, cls._NAME)
        if friendly is not None:
            return kls(friendly)
        return kls(f"{cls._NAME}: {msg}")

    @staticmethod
    def _normalize(code):
        return code

def retry_after_seconds(resp):
    raw = resp.headers.get("Retry-After")
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    return n if n > 0 else None

async def raise_for_status(exchange, resp):
    name = exchange.value.capitalize()
    if resp.status >= 500:
        raise ExchangeUnavailableError(friendly_message(ExchangeUnavailableError, name) or "")
    if resp.status in (418, 429):
        raise RateLimitError(friendly_message(RateLimitError, name) or "", retry_after=retry_after_seconds(resp))
    if resp.status == 403:
        raise IpNotWhitelistedError(friendly_message(IpNotWhitelistedError, name) or "")
