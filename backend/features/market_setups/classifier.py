from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from domain.enums import Exchange, MarketType
from exchanges.types import Kline

SETUPS = ("trend_pullback", "breakout", "range_fade", "reversal", "news_volatility")
UNDEFINED = "undefined"

LOOKBACK_BARS = 20
_ATR_BARS = 14
_ZERO = Decimal(0)
_HALF = Decimal("0.5")
_ONE = Decimal(1)

@dataclass(frozen=True, slots=True)
class _Signals:
    sma: Decimal
    atr: Decimal
    donchian_high: Decimal
    donchian_low: Decimal
    close_pos: Decimal
    vol_ratio: Decimal
    bar_range: Decimal
    above_sma: bool
    bullish: bool

def _measure(window: list[Kline]) -> _Signals:
    last = window[-1]
    high = max(c.high for c in window)
    low = min(c.low for c in window)
    span = high - low
    recent = window[-_ATR_BARS:]
    sma = sum(c.close for c in window) / Decimal(len(window))
    avg_vol = sum(c.volume for c in window) / Decimal(len(window))
    return _Signals(
        sma=sma,
        atr=sum(c.high - c.low for c in recent) / Decimal(len(recent)),
        donchian_high=high,
        donchian_low=low,
        close_pos=(last.close - low) / span if span > _ZERO else _HALF,
        vol_ratio=last.volume / avg_vol if avg_vol > _ZERO else _ONE,
        bar_range=last.high - last.low,
        above_sma=last.close > sma,
        bullish=last.close >= last.open
    )

def _label(s: _Signals) -> str:
    if s.vol_ratio >= Decimal(3) and s.atr > _ZERO and s.bar_range >= s.atr * Decimal(2):
        return "news_volatility"
    if s.vol_ratio >= Decimal("1.5") and (s.close_pos >= Decimal("0.9") or s.close_pos <= Decimal("0.1")):
        return "breakout"
    if s.close_pos <= Decimal("0.3") and s.above_sma and s.bullish:
        return "reversal"
    if s.close_pos >= Decimal("0.7") and not s.above_sma and not s.bullish:
        return "reversal"
    if s.atr > _ZERO and (s.donchian_high - s.donchian_low) >= s.atr * Decimal(4) and Decimal("0.3") < s.close_pos < Decimal("0.7"):
        return "trend_pullback"
    return "range_fade"

def classify(candles: list[Kline]) -> tuple[str, dict]:
    if len(candles) < LOOKBACK_BARS:
        return UNDEFINED, {"reason": "insufficient_history", "bars": len(candles)}

    s = _measure(candles[-LOOKBACK_BARS:])
    context = {
        "sma": str(s.sma), "atr": str(s.atr),
        "donchian_high": str(s.donchian_high), "donchian_low": str(s.donchian_low),
        "close_pos": str(s.close_pos), "vol_ratio": str(s.vol_ratio)
    }
    return _label(s), context

def classify_rows(exchange: Exchange, market_type: MarketType, symbol: str, candles: list[Kline], last_setup_ms: int) -> list[dict]:
    rows = []
    for i in range(LOOKBACK_BARS - 1, len(candles)):
        bar = candles[i]
        if bar.time_ms <= last_setup_ms:
            continue
        setup, context = classify(candles[i - LOOKBACK_BARS + 1: i + 1])
        rows.append({
            "exchange": exchange, "market_type": market_type, "symbol": symbol,
            "time": datetime.fromtimestamp(bar.time_ms / 1000, tz=timezone.utc),
            "setup": setup, "context": context
        })
    return rows
