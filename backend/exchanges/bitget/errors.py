from shared.exceptions import (
    InvalidCredentialsError, IpNotWhitelistedError,
    KeyAccessRestrictedError, RateLimitError
)

from ..errors import ExchangeErrors

class BitgetErrors(ExchangeErrors):
    _NAME = "Bitget"
    _CODES = {
        "1001": RateLimitError,
        "30014": RateLimitError,
        "40001": InvalidCredentialsError,
        "40002": InvalidCredentialsError,
        "40003": InvalidCredentialsError,
        "40004": InvalidCredentialsError,
        "40005": InvalidCredentialsError,
        "40006": InvalidCredentialsError,
        "40009": InvalidCredentialsError,
        "40010": InvalidCredentialsError,
        "40011": InvalidCredentialsError,
        "40012": InvalidCredentialsError,
        "40014": KeyAccessRestrictedError,
        "40018": IpNotWhitelistedError,
        "40037": InvalidCredentialsError
    }
    _PASSPHRASE_CODES = ("40012",)

    @staticmethod
    def _normalize(code):
        return str(code)
