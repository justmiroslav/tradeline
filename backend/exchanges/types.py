from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from domain.enums import Exchange, MarketType, TradeSide

@dataclass(frozen=True, slots=True)
class SignedRequest:
    url: str
    headers: dict
    body: bytes | None = None

@dataclass(frozen=True, slots=True)
class BucketSpec:
    capacity: int
    refill_per_sec: float
    header_remaining_key: str | None = None
    header_used_key: str | None = None
    per_ip: bool = True

@dataclass(slots=True)
class NormalizedTrade:
    id: str
    exchange: Exchange
    market_type: MarketType
    symbol: str
    time: datetime
    price: Decimal
    quantity: Decimal
    side: TradeSide
    fee: Decimal | None
    fee_asset: str | None = None
    order_id: str | None = None
    realized_pnl: Decimal | None = None
    is_maker: bool | None = None
    quote_qty: Decimal | None = None
    position_side: str | None = None

    @property
    def volume(self):
        return self.price * self.quantity

    def to_payload(self):
        return {
            "id": self.id,
            "exchange": self.exchange.value,
            "market_type": self.market_type.value,
            "symbol": self.symbol,
            "side": self.side.value,
            "price": str(self.price),
            "quantity": str(self.quantity),
            "quote_qty": str(self.quote_qty) if self.quote_qty is not None else None,
            "fee": str(self.fee) if self.fee is not None else None,
            "fee_asset": self.fee_asset,
            "order_id": self.order_id,
            "realized_pnl": str(self.realized_pnl) if self.realized_pnl is not None else None,
            "is_maker": self.is_maker,
            "position_side": self.position_side,
            "time": self.time.isoformat()
        }

@dataclass(frozen=True, slots=True)
class KeyCapabilities:
    spot: bool
    futures: bool
    account_uid: str | None = None
    ip_restricted: bool = False

    def as_list(self):
        out = []
        if self.spot:
            out.append("spot")
        if self.futures:
            out.append("futures")
        return out

@dataclass(frozen=True, slots=True)
class Kline:
    time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

@dataclass(frozen=True, slots=True)
class DecryptedCredentials:
    api_key: str
    api_secret: str
    passphrase: str | None = None
