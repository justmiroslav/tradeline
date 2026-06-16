import aiohttp

from domain.enums import Exchange, MarketType

from .binance import BinanceClient
from .bitget import BitgetClient
from .bybit import BybitClient
from .client import BaseExchangeClient
from .http_executor import RequestExecutor
from .okx import OKXClient
from .proxy_pool import ProxyRouter
from .types import DecryptedCredentials, Kline

_CLIENTS = {
    Exchange.BINANCE: BinanceClient,
    Exchange.BYBIT: BybitClient,
    Exchange.BITGET: BitgetClient,
    Exchange.OKX: OKXClient
}

class ExchangeGateway:
    def __init__(self, session: aiohttp.ClientSession, router: ProxyRouter):
        self._executors = {
            exchange: RequestExecutor(exchange, session, router)
            for exchange in _CLIENTS
        }
        self._public = {
            exchange: cls(self._executors[exchange])
            for exchange, cls in _CLIENTS.items()
        }

    def executor(self, exchange: Exchange) -> RequestExecutor:
        return self._executors[exchange]

    def client(self, exchange: Exchange, api_key: str, api_secret: str, passphrase: str | None = None) -> BaseExchangeClient:
        cls = _CLIENTS.get(exchange)
        if cls is None:
            raise NotImplementedError(f"{exchange.value} client not implemented")
        return cls(self._executors[exchange], DecryptedCredentials(api_key, api_secret, passphrase))

    async def fetch_klines_range(self, exchange: Exchange, market_type: MarketType, symbol: str, start_ms: int, end_ms: int) -> list[Kline]:
        return await self._public[exchange].fetch_klines_range(market_type, symbol, start_ms, end_ms)

    async def fetch_binance_tickers(self, symbols: list[str] | None = None) -> list:
        return await self._public[Exchange.BINANCE].fetch_ticker_24h(symbols)
