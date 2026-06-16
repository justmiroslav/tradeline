from decimal import Decimal as D
from types import SimpleNamespace

from domain.enums import MarketType
from exchanges.bybit.rest import BybitClient

class _FakeBybit(BybitClient):
    def __init__(self):
        self.calls = 0

    async def _closed_pnl_map(self):
        self.calls += 1
        return {"o1": D("5")}

class TestBybitEnrich:
    async def test_pnl_map_built_once_across_pages(self):
        client = _FakeBybit()
        page1 = [SimpleNamespace(order_id="o1", realized_pnl=None)]
        page2 = [SimpleNamespace(order_id="o1", realized_pnl=None)]
        await client.enrich_trades(MarketType.FUTURES, page1)
        await client.enrich_trades(MarketType.FUTURES, page2)
        assert client.calls == 1
        assert page1[0].realized_pnl == D("5")

    async def test_spot_market_is_not_enriched(self):
        client = _FakeBybit()
        await client.enrich_trades(MarketType.SPOT, [SimpleNamespace(order_id="o1", realized_pnl=None)])
        assert client.calls == 0
