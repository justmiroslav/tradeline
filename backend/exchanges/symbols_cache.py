import asyncio

from domain.enums import Exchange, MarketType
from utils.logger import logger

from .gateway import ExchangeGateway
from .symbols import PUBLIC_SYMBOL_FETCHERS

class SymbolCache:
    _REFRESH_INTERVAL = 12 * 3600
    _RETRY_INTERVAL = 300

    def __init__(self, gateway: ExchangeGateway):
        self._gateway = gateway
        self._cache = {}
        self._task = None

    def start(self):
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def get(self, exchange: Exchange, market_type: MarketType) -> list:
        return self._cache.get((exchange, market_type), [])

    def has(self, exchange: Exchange, market_type: MarketType) -> bool:
        return (exchange, market_type) in self._cache

    async def wait_for(self, exchange: Exchange, market_type: MarketType, timeout: int = 20) -> bool:
        for _ in range(timeout * 2):
            if self.has(exchange, market_type):
                return True
            await asyncio.sleep(0.5)
        return self.has(exchange, market_type)

    async def _loop(self):
        while True:
            loaded = await self._refresh_all()
            await asyncio.sleep(self._REFRESH_INTERVAL if loaded else self._RETRY_INTERVAL)

    async def _refresh_all(self) -> bool:
        results = await asyncio.gather(*[
            self._refresh_one(exchange, mt)
            for exchange in PUBLIC_SYMBOL_FETCHERS
            for mt in MarketType
        ])
        return all(results)

    async def _refresh_one(self, exchange: Exchange, market_type: MarketType) -> bool:
        try:
            symbols = await PUBLIC_SYMBOL_FETCHERS[exchange](market_type, self._gateway.executor(exchange))
            self._cache[(exchange, market_type)] = symbols
            logger.info(f"[SymbolCache] {exchange.value}/{market_type.value}: {len(symbols)} symbols")
            return True
        except Exception as e:
            logger.warning(f"[SymbolCache] {exchange.value}/{market_type.value} load failed: {e}")
            self._cache.setdefault((exchange, market_type), [])
            return False
