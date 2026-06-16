from datetime import timezone
from decimal import Decimal

from domain.enums import MarketType, TradeSide
from exchanges.binance.rest import BinanceClient
from exchanges.bitget.rest import parse_rest_fill as bitget_parse
from exchanges.bybit.rest import parse_execution as bybit_parse
from exchanges.okx.rest import parse_rest_fill as okx_parse

class TestParsers:
    def test_binance_futures_side_field_and_realized_pnl(self):
        row = {"id": 99, "orderId": 3, "symbol": "BTCUSDT", "price": "30000", "qty": "0.1",
               "quoteQty": "3000", "commission": "0.5", "commissionAsset": "USDT",
               "time": 1700000000000, "side": "BUY", "maker": False, "realizedPnl": "1.0"}
        t = BinanceClient._parse(row, MarketType.FUTURES)
        assert t.side == TradeSide.BUY and t.realized_pnl == Decimal("1.0") and t.fee == Decimal("0.5")
        assert t.time.tzinfo is timezone.utc

    def test_binance_spot_uses_isbuyer_and_missing_commission_is_none(self):
        row = {"id": 1, "orderId": 2, "symbol": "X", "price": "1", "qty": "1", "quoteQty": "1",
               "time": 1700000000000, "isBuyer": False, "isMaker": True}
        t = BinanceClient._parse(row, MarketType.SPOT)
        assert t.side == TradeSide.SELL and t.fee is None

    def test_okx_negative_fee_normalised_and_billid_fallback(self):
        row = {"tradeId": "", "billId": "B", "instId": "BTC-USDT", "ordId": "o",
               "fillPx": "100", "fillSz": "0.5", "fee": "-0.1", "feeCcy": "USDT",
               "side": "buy", "ts": "1700000000000", "execType": "T"}
        t = okx_parse(row, MarketType.SPOT)
        assert t.id == "B"
        assert t.fee == Decimal("0.1")
        assert t.symbol == "BTCUSDT"

    def test_okx_swap_inst_id_is_unified(self):
        row = {"tradeId": "T", "billId": "B", "instId": "ETH-USDT-SWAP", "ordId": "o",
               "fillPx": "3000", "fillSz": "1", "fee": "-0.5", "feeCcy": "USDT",
               "side": "sell", "ts": "1700000000000", "execType": "M", "fillPnl": "12"}
        t = okx_parse(row, MarketType.FUTURES)
        assert t.symbol == "ETHUSDT"
        assert t.realized_pnl == Decimal("12")

    def test_bybit_side_and_fee(self):
        row = {"execId": "x", "orderId": "o", "symbol": "ETHUSDT", "execPrice": "3000",
               "execQty": "1", "execFee": "0.1", "execTime": "1700000000000", "side": "Sell", "isMaker": True}
        t = bybit_parse(row, MarketType.FUTURES)
        assert t.side == TradeSide.SELL and t.fee == Decimal("0.1") and t.market_type == MarketType.FUTURES

    def test_bitget_futures_fee_as_list_and_profit_as_pnl(self):
        row = {"tradeId": "T", "orderId": "o", "symbol": "ETHUSDT", "price": "3000",
               "baseVolume": "1", "feeDetail": [{"totalFee": "-1.5", "feeCoin": "USDT"}],
               "side": "sell", "cTime": "1700000000000", "tradeScope": "maker", "profit": "5.0"}
        t = bitget_parse(row, MarketType.FUTURES)
        assert t.fee == Decimal("1.5") and t.realized_pnl == Decimal("5.0")
