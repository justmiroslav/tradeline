from typing import Any

import pytest

from domain.enums import Exchange
from exchanges.binance.errors import BinanceErrors
from exchanges.bitget.errors import BitgetErrors
from exchanges.bybit.errors import BybitErrors
from exchanges.errors import raise_for_status, retry_after_seconds
from exchanges.okx.errors import OKXErrors
from shared.exceptions import (
    ExchangeError, ExchangeUnavailableError, InvalidCredentialsError,
    IpNotWhitelistedError, KeyAccessRestrictedError, RateLimitError
)

class _Resp:
    def __init__(self, status: int, headers: dict | None = None) -> None:
        self.status = status
        self.headers = headers or {}

def _r(status: int, headers: dict | None = None) -> Any:
    return _Resp(status, headers)

class TestErrorParsers:
    def test_representative_codes_map_to_the_right_class(self):
        assert isinstance(BinanceErrors.parse(-1022, "m"), InvalidCredentialsError)
        assert isinstance(BinanceErrors.parse(-1003, "m"), RateLimitError)
        assert isinstance(BybitErrors.parse(10003, "m"), InvalidCredentialsError)
        assert isinstance(BybitErrors.parse(10010, "m"), IpNotWhitelistedError)
        assert isinstance(OKXErrors.parse("50104", "m"), InvalidCredentialsError)
        assert isinstance(BitgetErrors.parse("40014", "m"), KeyAccessRestrictedError)

    def test_binance_minus_2015_splits_ip_vs_credentials_by_message(self):
        ip = BinanceErrors.parse(-2015, "Invalid API-key, IP, or permissions for action, request ip: 1.2.3.4")
        assert isinstance(ip, IpNotWhitelistedError)
        assert isinstance(BinanceErrors.parse(-2015, "Invalid API-key"), InvalidCredentialsError)

    def test_unknown_and_non_numeric_codes_fall_back_to_base(self):
        assert type(BinanceErrors.parse(-9999, "weird")) is ExchangeError
        assert isinstance(OKXErrors.parse("not-a-number", "weird"), ExchangeError)

class TestRaiseForStatus:
    async def test_status_codes_map_to_errors(self):
        with pytest.raises(ExchangeUnavailableError):
            await raise_for_status(Exchange.BINANCE, _r(503))
        with pytest.raises(IpNotWhitelistedError):
            await raise_for_status(Exchange.OKX, _r(403))
        with pytest.raises(RateLimitError) as ei:
            await raise_for_status(Exchange.BYBIT, _r(429, {"Retry-After": "5"}))
        assert ei.value.retry_after == 5

    async def test_2xx_and_plain_4xx_do_not_raise(self):
        await raise_for_status(Exchange.BINANCE, _r(200))
        await raise_for_status(Exchange.BINANCE, _r(400))

class TestRetryAfter:
    def test_numeric_then_missing_then_non_numeric(self):
        assert retry_after_seconds(_r(429, {"Retry-After": "10"})) == 10
        assert retry_after_seconds(_r(429)) is None
        assert retry_after_seconds(_r(429, {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})) is None
