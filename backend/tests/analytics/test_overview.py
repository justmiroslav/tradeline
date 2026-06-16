from datetime import datetime, timezone
from decimal import Decimal as D

import pytest

from domain.enums import Exchange, MarketType, PositionSide, PositionStatus
from domain.models import Position
from features.analytics.compute import compute_overview

def _pos(pnl, fee, symbol, setup, open_h, close_h, averaged_down=False, mfe=None, mae=None, status=PositionStatus.CLOSED, market=MarketType.SPOT):
    return Position(
        realized_pnl=D(pnl), fees_quote=D(fee), qty=D(1), entry_price=D(100), entry_notional=D(100),
        exchange=Exchange.BINANCE, market_type=market, symbol=symbol, setup=setup,
        side=PositionSide.LONG, status=status, trade_count=2,
        opened_at=datetime(2026, 4, 1, open_h, tzinfo=timezone.utc),
        closed_at=datetime(2026, 4, 1, close_h, tzinfo=timezone.utc),
        averaged_down=averaged_down, mfe=mfe, mae=mae
    )

_SAMPLE = [
    _pos("100", "10", "BTC", "breakout", 10, 11, mfe=D("0.05"), mae=D("0.02")),
    _pos("-50", "5", "ETH", "reversal", 12, 13, averaged_down=True, mae=D("0.06")),
    _pos("20", "2", "BTC", "breakout", 14, 16)
]

@pytest.fixture(scope="module")
def overview():
    return compute_overview(_SAMPLE, [])

class TestKpis:
    def test_core_kpis(self, overview):
        k = overview.kpis
        assert k.net_pnl == "53"
        assert round(k.win_rate, 3) == 0.667
        assert round(k.profit_factor, 2) == 1.96
        assert k.expectancy == str(D(53) / 3)
        assert k.total_positions == 3
        assert k.total_volume == "300"

    def test_drawdown_and_streaks(self, overview):
        k = overview.kpis
        assert k.max_drawdown == "55"
        assert k.win_streak == 1 and k.loss_streak == 1
        assert k.largest_win == "90" and k.largest_loss == "-55"

class TestBreakdowns:
    def test_by_symbol_aggregates_and_sorts_by_net(self, overview):
        by_symbol = {b.key: b for b in overview.by_symbol}
        assert by_symbol["BTC"].net_pnl == "108"
        assert by_symbol["BTC"].volume == "200"
        assert by_symbol["ETH"].net_pnl == "-55"
        assert overview.by_symbol[0].key == "BTC"

    def test_by_setup_win_rate(self, overview):
        by_setup = {b.key: b for b in overview.by_setup}
        assert by_setup["breakout"].count == 2 and by_setup["breakout"].win_rate == 1.0
        assert by_setup["reversal"].win_rate == 0.0

    def test_by_market_splits_spot_and_futures(self):
        o = compute_overview([
            _pos("100", "0", "BTC", "x", 10, 11),
            _pos("-30", "0", "ETH", "x", 12, 13, market=MarketType.FUTURES)
        ], [])
        by_market = {b.key: b for b in o.by_market}
        assert by_market["spot"].net_pnl == "100"
        assert by_market["futures"].net_pnl == "-30" and by_market["futures"].count == 1

class TestMetrics:
    def test_averaging_split(self, overview):
        a = overview.averaging
        assert a.averaged_down_count == 1 and a.rest_count == 2
        assert a.averaged_down_net == "-55"

    def test_excursion_aggregates_winner_mfe_loser_mae(self, overview):
        e = overview.excursion
        assert e.avg_winner_mfe == 0.05
        assert e.avg_loser_mae == 0.06

    def test_open_exposure(self):
        opened = [_pos("0", "0", "BTC", None, 9, 9, status=PositionStatus.OPEN)]
        o = compute_overview(_SAMPLE, opened)
        assert o.open_exposure.count == 1 and o.open_exposure.notional == "100"

class TestTimeAndDuration:
    def test_by_hour_buckets_on_close_time(self, overview):
        assert {b.key for b in overview.by_hour} == {"11", "13", "16"}

    def test_daily_pnl_and_equity_curve(self, overview):
        assert len(overview.daily_pnl) == 1 and overview.daily_pnl[0].net_pnl == "53"
        assert [e.equity for e in overview.equity_curve] == ["90", "35", "53"]

    def test_hold_duration_splits_win_vs_loss(self, overview):
        d = overview.duration
        assert d.avg_win_minutes == 90.0 and d.avg_loss_minutes == 60.0

class TestEdgeCases:
    def test_empty_is_a_zeroed_overview(self):
        o = compute_overview([], [])
        assert o.kpis.net_pnl == "0" and o.kpis.win_rate == 0.0 and o.kpis.total_positions == 0
        assert o.kpis.profit_factor is None and o.by_symbol == [] and o.equity_curve == []

    def test_all_wins_has_undefined_profit_factor(self):
        o = compute_overview([_pos("100", "0", "BTC", "x", 10, 11), _pos("50", "0", "ETH", "x", 12, 13)], [])
        assert o.kpis.profit_factor is None
        assert o.kpis.win_rate == 1.0 and o.kpis.loss_streak == 0

    def test_breakeven_counts_as_non_win(self):
        o = compute_overview([_pos("10", "10", "BTC", "x", 10, 11)], [])
        assert o.kpis.win_rate == 0.0
