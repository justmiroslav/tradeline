from decimal import Decimal as D

from exchanges.types import Kline
from features.market_setups.classifier import classify

_BAR = 15 * 60 * 1000

def _mk(closes, highs=None, lows=None, vols=None):
    n = len(closes)
    highs = highs if highs is not None else [c + 1 for c in closes]
    lows = lows if lows is not None else [c - 1 for c in closes]
    vols = vols if vols is not None else [1] * n
    return [
        Kline(time_ms=i * _BAR, open=D(closes[i]), high=D(highs[i]), low=D(lows[i]), close=D(closes[i]), volume=D(vols[i]))
        for i in range(n)
    ]

class TestClassify:
    def test_insufficient_history_is_undefined(self):
        assert classify(_mk([100] * 19))[0] == "undefined"

    def test_flat_market_is_range_fade(self):
        assert classify(_mk([100] * 20))[0] == "range_fade"

    def test_volume_spike_wide_bar_is_news_volatility(self):
        window = _mk([100] * 20, highs=[101] * 19 + [120], lows=[99] * 19 + [80], vols=[1] * 19 + [20])
        assert classify(window)[0] == "news_volatility"

    def test_close_at_range_high_on_volume_is_breakout(self):
        window = _mk([100] * 19 + [105], highs=[101] * 19 + [105], lows=[99] * 19 + [100], vols=[1] * 19 + [2])
        assert classify(window)[0] == "breakout"

    def test_deep_wick_closing_above_mean_is_reversal(self):
        window = _mk([90] * 19 + [93], highs=[91] * 19 + [105])
        assert classify(window)[0] == "reversal"

    def test_wide_range_with_calm_pullback_is_trend_pullback(self):
        closes = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111]
        assert classify(_mk(closes))[0] == "trend_pullback"

    def test_context_carries_signal_values(self):
        setup, context = classify(_mk([100] * 20))
        assert {"sma", "atr", "donchian_high", "donchian_low", "close_pos", "vol_ratio"} <= context.keys()
