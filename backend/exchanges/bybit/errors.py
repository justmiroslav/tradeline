from shared.exceptions import (
    InvalidCredentialsError, IpNotWhitelistedError,
    KeyAccessRestrictedError, RateLimitError
)

from ..errors import ExchangeErrors

class BybitErrors(ExchangeErrors):
    _NAME = "Bybit"
    _CODES = {
        10002: InvalidCredentialsError,
        10003: InvalidCredentialsError,
        10004: InvalidCredentialsError,
        10005: KeyAccessRestrictedError,
        10006: RateLimitError,
        10007: InvalidCredentialsError,
        10008: InvalidCredentialsError,
        10009: IpNotWhitelistedError,
        10010: IpNotWhitelistedError,
        10018: RateLimitError,
        33004: InvalidCredentialsError
    }

    @staticmethod
    def _normalize(code):
        return int(code) if str(code).lstrip("-").isdigit() else 0
