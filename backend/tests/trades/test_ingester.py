from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

from domain.enums import Exchange, MarketType, TradeSide
from exchanges.types import NormalizedTrade
from features.trades.ingester import TradeIngester

def _trade(age_seconds: int) -> NormalizedTrade:
    return NormalizedTrade(
        id=f"t-{age_seconds}", exchange=Exchange.BYBIT, market_type=MarketType.FUTURES, symbol="BTCUSDT",
        time=datetime.now(timezone.utc) - timedelta(seconds=age_seconds),
        price=D(100), quantity=D(1), side=TradeSide.BUY, fee=None
    )

class TestLiveSkewClassification:
    def test_fresh_fills_count_as_live_appends(self):
        assert TradeIngester._is_backdated([_trade(5), _trade(30)]) is False

    def test_stale_fill_counts_as_history_change(self):
        assert TradeIngester._is_backdated([_trade(5), _trade(120)]) is True

    def test_empty_batch_is_live(self):
        assert TradeIngester._is_backdated([]) is False
