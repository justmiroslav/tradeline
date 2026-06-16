from typing import Any
from unittest.mock import AsyncMock, patch

from domain.enums import MarketType
from exchanges.okx.rest import OKXClient, to_inst_id, to_symbol
from exchanges.types import DecryptedCredentials

_NO_EXEC: Any = None

class TestOkxSymbolMapping:
    def test_native_to_unified(self):
        assert to_symbol("BTC-USDT") == "BTCUSDT"
        assert to_symbol("ETH-USDT-SWAP") == "ETHUSDT"
        assert to_symbol("1000PEPE-USDT-SWAP") == "1000PEPEUSDT"

    def test_unified_to_native(self):
        assert to_inst_id("BTCUSDT", MarketType.SPOT) == "BTC-USDT"
        assert to_inst_id("ETHUSDT", MarketType.FUTURES) == "ETH-USDT-SWAP"

    def test_round_trip(self):
        for symbol in ("BTCUSDT", "SOLUSDT", "1000PEPEUSDT"):
            for mt in MarketType:
                assert to_symbol(to_inst_id(symbol, mt)) == symbol

    async def test_klines_request_sends_native_inst_id(self):
        client = OKXClient(_NO_EXEC, DecryptedCredentials("k", "s", "p"))
        captured = {}

        async def fake(method, base, path, pool, params=None, **_):
            captured.update(params or {})
            return {"code": "0", "data": []}

        with patch.object(client, "_request", new=AsyncMock(side_effect=fake)):
            await client.fetch_klines(MarketType.FUTURES, "SOLUSDT", 0, 1000)
        assert captured["instId"] == "SOL-USDT-SWAP"
