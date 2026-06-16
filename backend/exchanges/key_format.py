import re

from domain.enums import Exchange
from shared.exceptions import InvalidCredentialsError

_BINANCE_TOKEN = re.compile(r"[A-Za-z0-9]{40,80}")
_BITGET_PASS = re.compile(r"[A-Za-z0-9]{8,32}")

def validate_key_format(exchange: Exchange, api_key: str, api_secret: str, passphrase: str | None) -> None:
    key = (api_key or "").strip()
    secret = (api_secret or "").strip()
    pw = (passphrase or "").strip()

    if exchange is Exchange.BINANCE:
        if not _BINANCE_TOKEN.fullmatch(key) or not _BINANCE_TOKEN.fullmatch(secret):
            raise InvalidCredentialsError("Check the Binance key and secret — each is 64 letters and numbers, no spaces")
    elif exchange is Exchange.BYBIT:
        if len(key) < 10 or len(secret) < 20:
            raise InvalidCredentialsError("Check the Bybit key and secret — that doesn't look right")
    elif exchange is Exchange.OKX:
        if len(key) < 20 or len(secret) < 16:
            raise InvalidCredentialsError("Check the OKX key and secret — that doesn't look right")
        if not pw:
            raise InvalidCredentialsError("Add the passphrase you set when creating the OKX key")
    elif exchange is Exchange.BITGET:
        if not key.startswith("bg_"):
            raise InvalidCredentialsError("Bitget keys start with bg_ — check the key")
        if len(secret) < 16:
            raise InvalidCredentialsError("Check the Bitget secret — that doesn't look right")
        if not _BITGET_PASS.fullmatch(pw):
            raise InvalidCredentialsError("Add the 8-32 character passphrase from your Bitget key")
