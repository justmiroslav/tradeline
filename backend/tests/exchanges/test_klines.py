from datetime import datetime, timezone
from decimal import Decimal as D
from typing import Any
from unittest.mock import AsyncMock, patch

from domain.enums import MarketType
from exchanges.bitget.rest import BitgetClient
from exchanges.client import BaseExchangeClient
from exchanges.okx.rest import OKXClient
from exchanges.types import DecryptedCredentials, Kline

_BAR = 15 * 60 * 1000
_BARS = [i * _BAR for i in range(10)]
_NO_EXEC: Any = None

class _FakeClient(BaseExchangeClient):
    exchange = None

    def __init__(self, bars, newest_first, page):
        self._bars = bars
        self._KLINE_NEWEST_FIRST = newest_first
        self._page = page

    def fetch_mode(self, market_type):
        return "cursor"

    async def validate_credentials(self):
        ...

    def _build_request(self, *args):
        ...

    async def fetch_klines(self, market_type, symbol, lo, hi):
        window = [t for t in self._bars if lo <= t <= hi]
        chunk = window[-self._page:] if self._KLINE_NEWEST_FIRST else window[:self._page]
        return [Kline(time_ms=t, open=D(1), high=D(1), low=D(1), close=D(1), volume=D(1)) for t in chunk]

class TestKlinesRange:
    async def test_forward_pagination_covers_full_range_ascending(self):
        out = await _FakeClient(_BARS, newest_first=False, page=3).fetch_klines_range(MarketType.SPOT, "X", _BARS[0], _BARS[-1])
        assert [k.time_ms for k in out] == _BARS

    async def test_backward_pagination_covers_full_range_ascending(self):
        out = await _FakeClient(_BARS, newest_first=True, page=3).fetch_klines_range(MarketType.SPOT, "X", _BARS[0], _BARS[-1])
        assert [k.time_ms for k in out] == _BARS

    async def test_terminates_when_source_is_exhausted(self):
        out = await _FakeClient([_BARS[0]], newest_first=False, page=1).fetch_klines_range(MarketType.SPOT, "X", _BARS[0], _BARS[-1])
        assert [k.time_ms for k in out] == [_BARS[0]]

class TestBitgetKlines:
    async def test_history_candles_anchored_at_end_time_and_floored_at_start(self):
        c = BitgetClient(_NO_EXEC, DecryptedCredentials("k", "s", "p"))
        rows = [[str(t * _BAR), "1", "1", "1", "1", "1", "1", "1"] for t in range(4)]
        mock = AsyncMock(return_value={"code": "00000", "data": rows})

        with patch.object(c, "_request", new=mock):
            out = await c.fetch_klines(MarketType.FUTURES, "BTCUSDT", 2 * _BAR, 3 * _BAR)

        path, params = mock.call_args.args[2], mock.call_args.args[4]
        assert path == c._FUTURES_HISTORY_CANDLES
        assert params["endTime"] == str(3 * _BAR) and params["limit"] == "200"
        assert "startTime" not in params
        assert [k.time_ms for k in out] == [2 * _BAR, 3 * _BAR]

    async def test_spot_uses_spot_history_endpoint(self):
        c = BitgetClient(_NO_EXEC, DecryptedCredentials("k", "s", "p"))
        mock = AsyncMock(return_value={"code": "00000", "data": []})

        with patch.object(c, "_request", new=mock):
            await c.fetch_klines(MarketType.SPOT, "BTCUSDT", 0, _BAR)

        path, params = mock.call_args.args[2], mock.call_args.args[4]
        assert path == c._SPOT_HISTORY_CANDLES
        assert params["granularity"] == "15min" and "productType" not in params

class TestOKXKlines:
    async def test_recent_window_uses_live_candles(self):
        c = OKXClient(_NO_EXEC, DecryptedCredentials("k", "s", "p"))
        mock = AsyncMock(return_value={"code": "0", "data": []})
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        with patch.object(c, "_request", new=mock):
            await c.fetch_klines(MarketType.FUTURES, "BTCUSDT", now_ms - _BAR, now_ms)

        assert mock.call_args.args[2] == c._CANDLES
        assert mock.call_args.args[4]["instId"] == "BTC-USDT-SWAP"

    async def test_old_window_uses_history_candles(self):
        c = OKXClient(_NO_EXEC, DecryptedCredentials("k", "s", "p"))
        mock = AsyncMock(return_value={"code": "0", "data": []})
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        with patch.object(c, "_request", new=mock):
            await c.fetch_klines(MarketType.SPOT, "BTCUSDT", now_ms - 90 * 86400 * 1000, now_ms)

        assert mock.call_args.args[2] == c._HISTORY_CANDLES
