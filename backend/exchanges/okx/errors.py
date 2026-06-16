from shared.exceptions import (
    ExchangeUnavailableError, InvalidCredentialsError,
    IpNotWhitelistedError, RateLimitError
)

from ..errors import ExchangeErrors

class OKXErrors(ExchangeErrors):
    _NAME = "OKX"
    _CODES = {
        50001: ExchangeUnavailableError,
        50005: ExchangeUnavailableError,
        50007: ExchangeUnavailableError,
        50011: RateLimitError,
        50061: RateLimitError,
        50101: InvalidCredentialsError,
        50102: InvalidCredentialsError,
        50103: InvalidCredentialsError,
        50104: InvalidCredentialsError,
        50105: InvalidCredentialsError,
        50107: InvalidCredentialsError,
        50110: IpNotWhitelistedError,
        50111: InvalidCredentialsError,
        50112: InvalidCredentialsError,
        50113: InvalidCredentialsError
    }
    _PASSPHRASE_CODES = (50104, 50105)

    @staticmethod
    def _normalize(code):
        return int(code) if str(code).lstrip("-").isdigit() else 0
