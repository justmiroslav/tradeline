from dataclasses import dataclass

from domain.enums import Exchange

from .types import BucketSpec

WS_HEARTBEAT = 20.0
BACKOFF_BASE = 1.0
BACKOFF_CAP = 60.0
BACKOFF_FLOOR = 0.5
WS_STABLE_SECONDS = 60.0

@dataclass(frozen=True, slots=True)
class ExchangeEndpoints:
    url: str
    ws: str
    futures_url: str = ""
    futures_ws: str = ""

ENDPOINTS = {
    Exchange.BINANCE: ExchangeEndpoints(
        url="https://api.binance.com",
        ws="wss://ws-api.binance.com/ws-api/v3",
        futures_url="https://fapi.binance.com",
        futures_ws="wss://fstream.binance.com/ws/"
    ),
    Exchange.BYBIT: ExchangeEndpoints(
        url="https://api.bybit.com",
        ws="wss://stream.bybit.com/v5/private"
    ),
    Exchange.OKX: ExchangeEndpoints(
        url="https://www.okx.com",
        ws="wss://ws.okx.com:8443/ws/v5/private"
    ),
    Exchange.BITGET: ExchangeEndpoints(
        url="https://api.bitget.com",
        ws="wss://ws.bitget.com/v2/ws/private"
    )
}

RATE_CONFIGS = {
    Exchange.BINANCE: {
        "spot": BucketSpec(6000, 80.0, header_used_key="X-MBX-USED-WEIGHT-1M"),
        "fut": BucketSpec(2400, 32.0, header_used_key="X-MBX-USED-WEIGHT-1M")
    },
    Exchange.BYBIT: {
        "trades": BucketSpec(5, 5.0, header_remaining_key="X-Bapi-Limit-Status", per_ip=False),
        "account": BucketSpec(10, 10.0, header_remaining_key="X-Bapi-Limit-Status", per_ip=False),
        "user": BucketSpec(10, 10.0, header_remaining_key="X-Bapi-Limit-Status", per_ip=False),
        "market": BucketSpec(50, 15.0)
    },
    Exchange.OKX: {
        "trades": BucketSpec(10, 5.0, header_remaining_key="X-RateLimit-Remaining", per_ip=False),
        "account": BucketSpec(5, 2.5, header_remaining_key="X-RateLimit-Remaining", per_ip=False),
        "market": BucketSpec(20, 8.0)
    },
    Exchange.BITGET: {
        "trades": BucketSpec(10, 10.0, per_ip=False),
        "account": BucketSpec(1, 0.5, per_ip=False),
        "market": BucketSpec(20, 10.0)
    }
}
