from abc import ABC, abstractmethod
from functools import partial

from domain.enums import MarketType
from shared.exceptions import ExchangeError, ExchangeUnavailableError
from utils.logger import brief, logger

from .helpers import FETCH_ERRORS, PROBE_FATAL_TYPES
from .http_executor import RequestExecutor
from .types import DecryptedCredentials, KeyCapabilities, Kline

class BaseExchangeClient(ABC):
    exchange = None
    _KLINE_BAR_MS = 15 * 60 * 1000
    _KLINE_NEWEST_FIRST = False

    def __init__(self, executor: RequestExecutor, creds: DecryptedCredentials | None = None):
        self._executor = executor
        self.api_key = creds.api_key if creds else ""
        self.api_secret = creds.api_secret if creds else ""
        self.passphrase = creds.passphrase if creds else None

    @abstractmethod
    def fetch_mode(self, market_type: MarketType) -> str: ...

    @abstractmethod
    async def validate_credentials(self): ...

    @abstractmethod
    def _build_request(self, method: str, base: str, path: str, params: dict, signed: bool): ...

    async def fetch_trades_paginated(self, market_type: MarketType, cursor: str | None = None):
        raise NotImplementedError

    async def fetch_trades_by_symbol(self, market_type: MarketType, symbol: str, since_id: str | None = None, start_ms: int | None = None):
        raise NotImplementedError

    async def fetch_klines(self, market_type: MarketType, symbol: str, start_ms: int, end_ms: int) -> list[Kline]:
        raise NotImplementedError

    async def fetch_klines_range(self, market_type: MarketType, symbol: str, start_ms: int, end_ms: int) -> list[Kline]:
        collected = {}
        back = self._KLINE_NEWEST_FIRST
        cursor = end_ms if back else start_ms

        while True:
            lo, hi = (start_ms, cursor) if back else (cursor, end_ms)
            if lo > hi:
                break

            batch = await self.fetch_klines(market_type, symbol, lo, hi)
            if not batch:
                break
            for k in batch:
                collected[k.time_ms] = k

            nxt = min(k.time_ms for k in batch) if back else max(k.time_ms for k in batch) + self._KLINE_BAR_MS
            if (nxt >= cursor) if back else (nxt <= cursor):
                break
            cursor = nxt

        return [collected[t] for t in sorted(collected)]

    async def fetch_scan_symbols(self, market_type: MarketType, universe: list):
        raise NotImplementedError

    async def fetch_spot_balances(self) -> dict:
        raise NotImplementedError

    async def enrich_trades(self, market_type: MarketType, trades: list):
        return

    def _check_payload(self, data):
        return None

    def _unwrap(self, data):
        return data

    async def _probe(self, base: str, path: str, pool: str, params: dict | None = None, weight: int = 1):
        try:
            await self._request("GET", base, path, pool, params or {}, weight=weight)
            return None
        except (*FETCH_ERRORS, ExchangeError) as e:
            return e

    async def _probe_data(self, base: str, path: str, pool: str, params: dict | None = None, weight: int = 1):
        try:
            data = await self._request("GET", base, path, pool, params or {}, weight=weight)
            return data, None
        except (*FETCH_ERRORS, ExchangeError) as e:
            return None, e

    def _log_validation(self, spot_err, fut_err, ip_restricted: bool) -> None:
        for market, err in (("spot", spot_err), ("futures", fut_err)):
            if err is not None:
                logger.info(f"[{self.exchange.value}] {market} probe failed: {brief(err)}")

    def _resolve_caps(self, *, spot_allowed: bool, spot_err, futures_allowed: bool, fut_err,
                      account_uid: str | None, ip_restricted: bool) -> KeyCapabilities:
        spot = spot_allowed and spot_err is None
        futures = futures_allowed and fut_err is None
        if not spot and not futures:
            raise self._both_failed(spot_err or fut_err, fut_err or spot_err)
        return KeyCapabilities(spot=spot, futures=futures, account_uid=account_uid, ip_restricted=ip_restricted)

    def _both_failed(self, spot_err: Exception, fut_err: Exception) -> Exception:
        for err in (spot_err, fut_err):
            if isinstance(err, PROBE_FATAL_TYPES):
                return err

        if isinstance(spot_err, ExchangeError):
            return spot_err

        return ExchangeUnavailableError(
            f"{self.exchange.value}: couldn't reach the API to validate the key — check the connection and retry"
        )

    async def _request(self, method: str, base: str, path: str, pool: str, params: dict | None = None, signed: bool = True, weight: int = 1):
        build = partial(self._build_request, method, base, path, params or {}, signed)
        data = await self._executor.request(method, build, pool, weight)
        self._check_payload(data)
        return self._unwrap(data)
