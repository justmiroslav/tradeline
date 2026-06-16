from enum import Enum

class Exchange(str, Enum):
    BINANCE = "binance"
    BYBIT = "bybit"
    BITGET = "bitget"
    OKX = "okx"

    @property
    def label(self) -> str:
        return _EXCHANGE_LABELS[self]

_EXCHANGE_LABELS = {
    Exchange.BINANCE: "Binance",
    Exchange.BYBIT: "Bybit",
    Exchange.BITGET: "Bitget",
    Exchange.OKX: "OKX"
}

class MarketType(str, Enum):
    SPOT = "spot"
    FUTURES = "futures"

class TradeSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"

class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    INCOMPLETE = "incomplete"

class FetchMode(str, Enum):
    SYMBOL_SCAN = "symbol_scan"
    CURSOR = "cursor"

class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
