from shared.exceptions import InvalidCredentialsError, IpNotWhitelistedError, RateLimitError

from ..errors import ExchangeErrors

class BinanceErrors(ExchangeErrors):
    _NAME = "Binance"
    _CODES = {
        -1003: RateLimitError,
        -1021: InvalidCredentialsError,
        -1022: InvalidCredentialsError,
        -2014: InvalidCredentialsError
    }

    @classmethod
    def parse(cls, code, msg):
        if code == -2015:
            if "request ip" in msg.lower():
                return IpNotWhitelistedError(
                    f"Binance: your current IP is not whitelisted on this key — {msg}. "
                    "Add it in Binance API Management, or remove the IP restriction"
                )
            return InvalidCredentialsError(f"Binance: {msg}")
        return super().parse(code, msg)
