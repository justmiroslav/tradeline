from datetime import datetime, timezone
from decimal import Decimal as D
from uuid import uuid4

from domain.enums import Exchange, MarketType, PositionSide, PositionStatus, TradeSide
from features.positions.engine import PositionsEngine, TradeEvent

_UID = uuid4()
_KID = uuid4()

class _FakeRepo:
    def __init__(self):
        self.positions = []

    async def find_open(self, user_id, api_key_id, exchange, market_type, symbol, side):
        key = (user_id, api_key_id, exchange, market_type, symbol, side, PositionStatus.OPEN)
        for p in self.positions:
            if (p.user_id, p.api_key_id, p.exchange, p.market_type, p.symbol, p.side, p.status) == key:
                return p
        return None

    def add(self, position):
        self.positions.append(position)

    @staticmethod
    async def flush():
        pass

def _trade(mt, sym, side, price, qty, day, pnl=None):
    return TradeEvent(
        user_id=_UID, api_key_id=_KID, exchange=Exchange.BINANCE, market_type=mt, symbol=sym,
        side=side, price=D(price), quantity=D(qty), fee=D(0),
        realized_pnl=D(pnl) if pnl is not None else None,
        time=datetime(2026, 4, day, tzinfo=timezone.utc), trade_id=f"t{day}"
    )

async def _run(trades):
    repo = _FakeRepo()
    engine = PositionsEngine(repo)
    for t in trades:
        await engine.apply(t)
    return repo.positions

class TestSpotFifo:
    async def test_fifo_pnl_nets_across_fills_and_flags_averaging_down(self):
        positions = await _run([
            _trade(MarketType.SPOT, "BTC", TradeSide.BUY, "100", "1", 1),
            _trade(MarketType.SPOT, "BTC", TradeSide.BUY, "90", "1", 2),
            _trade(MarketType.SPOT, "BTC", TradeSide.SELL, "95", "2", 3)
        ])
        assert len(positions) == 1
        p = positions[0]
        assert p.status == PositionStatus.CLOSED
        assert p.realized_pnl == D(0)
        assert p.averaged_down is True
        assert p.entry_notional == D(190)

    async def test_partial_close_leaves_position_open(self):
        positions = await _run([
            _trade(MarketType.SPOT, "BTC", TradeSide.BUY, "100", "2", 1),
            _trade(MarketType.SPOT, "BTC", TradeSide.SELL, "110", "1", 2)
        ])
        p = positions[0]
        assert p.status == PositionStatus.OPEN
        assert p.qty == D(1)
        assert p.realized_pnl == D(10)

    async def test_lead_in_sell_with_no_open_is_skipped(self):
        assert await _run([_trade(MarketType.SPOT, "BTC", TradeSide.SELL, "100", "1", 1)]) == []

class TestFutures:
    async def test_long_uses_exchange_realized_pnl(self):
        positions = await _run([
            _trade(MarketType.FUTURES, "ETH", TradeSide.BUY, "3000", "1", 1),
            _trade(MarketType.FUTURES, "ETH", TradeSide.SELL, "3200", "1", 2, pnl="200")
        ])
        p = positions[0]
        assert p.side == PositionSide.LONG and p.status == PositionStatus.CLOSED
        assert p.realized_pnl == D(200)

    async def test_short_opens_and_closes(self):
        positions = await _run([
            _trade(MarketType.FUTURES, "ETH", TradeSide.SELL, "3000", "1", 1),
            _trade(MarketType.FUTURES, "ETH", TradeSide.BUY, "2800", "1", 2, pnl="200")
        ])
        p = positions[0]
        assert p.side == PositionSide.SHORT and p.status == PositionStatus.CLOSED
        assert p.realized_pnl == D(200)

    async def test_orphan_close_with_pnl_is_skipped(self):
        assert await _run([_trade(MarketType.FUTURES, "ETH", TradeSide.SELL, "3000", "1", 1, pnl="50")]) == []

    async def test_long_close_without_exchange_pnl_derives_from_entry(self):
        positions = await _run([
            _trade(MarketType.FUTURES, "ETH", TradeSide.BUY, "3000", "1", 1),
            _trade(MarketType.FUTURES, "ETH", TradeSide.SELL, "3200", "1", 2)
        ])
        p = positions[0]
        assert p.status == PositionStatus.CLOSED
        assert p.realized_pnl == D(200)

    async def test_short_close_without_exchange_pnl_derives_from_entry(self):
        positions = await _run([
            _trade(MarketType.FUTURES, "ETH", TradeSide.SELL, "3000", "2", 1),
            _trade(MarketType.FUTURES, "ETH", TradeSide.BUY, "2800", "2", 2)
        ])
        p = positions[0]
        assert p.side == PositionSide.SHORT and p.status == PositionStatus.CLOSED
        assert p.realized_pnl == D(400)

    async def test_netting_flip_closes_then_opens_remainder(self):
        positions = await _run([
            _trade(MarketType.FUTURES, "ETH", TradeSide.SELL, "3000", "1", 1),
            _trade(MarketType.FUTURES, "ETH", TradeSide.BUY, "2900", "3", 2)
        ])
        assert len(positions) == 2
        closed = next(p for p in positions if p.status == PositionStatus.CLOSED)
        opened = next(p for p in positions if p.status == PositionStatus.OPEN)
        assert closed.side == PositionSide.SHORT
        assert opened.side == PositionSide.LONG and opened.qty == D(2) and opened.entry_price == D(2900)
        assert opened.entry_notional == D(5800)
