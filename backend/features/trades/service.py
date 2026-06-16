import asyncio

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.trade import TradeRepository
from domain.enums import FetchMode, MarketType, PlanTier
from domain.models import ApiKey
from domain.plans import history_months
from exchanges.client import BaseExchangeClient
from exchanges.helpers import FETCH_ERRORS
from exchanges.symbols_cache import SymbolCache
from exchanges.types import NormalizedTrade
from shared.exceptions import ExchangeError
from utils.logger import logger

class TradeService:
    _CONCURRENCY = 3
    _PAGE_FULL = 1000

    def __init__(self, session: AsyncSession, symbol_cache: SymbolCache):
        self.session = session
        self.symbol_cache = symbol_cache

    async def sync(self, api_key: ApiKey, client: BaseExchangeClient, tier: PlanTier,
                   since: datetime | None = None) -> list[NormalizedTrade]:
        now = datetime.now(timezone.utc)
        repo = TradeRepository(self.session)
        inserted: list[NormalizedTrade] = []

        for cap in api_key.capabilities:
            mt = MarketType.SPOT if cap == "spot" else MarketType.FUTURES
            plan_cutoff = now - timedelta(days=history_months(tier, api_key.exchange, mt) * 30)
            last = await repo.max_trade_time(api_key.id, mt)
            cutoff = max(c for c in (plan_cutoff, last, since) if c is not None)

            try:
                if client.fetch_mode(mt) == FetchMode.CURSOR:
                    batch = await self._sync_cursor(repo, api_key, client, mt, cutoff)
                else:
                    batch = await self._sync_symbol_scan(repo, api_key, client, mt, cutoff, full=last is None)
                inserted.extend(batch)
                logger.info(f"[{api_key.exchange.value}] {cap}: synced {len(batch)} trades (since {cutoff:%Y-%m-%d %H:%M})")
            except FETCH_ERRORS as e:
                logger.warning(f"[{api_key.exchange.value}] {cap} sync failed: {e}")

        return inserted

    @staticmethod
    async def _sync_cursor(repo: TradeRepository, api_key: ApiKey, client: BaseExchangeClient, market_type: MarketType, cutoff: datetime) -> list[NormalizedTrade]:
        collected: list[NormalizedTrade] = []
        cursor = None

        while True:
            trades, next_cursor = await client.fetch_trades_paginated(market_type, cursor)
            if not trades:
                break

            try:
                await client.enrich_trades(market_type, trades)
            except (*FETCH_ERRORS, ExchangeError) as e:
                logger.warning(f"[{api_key.exchange.value}] {market_type.value} enrich failed: {e}")

            collected.extend(await repo.upsert_many(api_key.user_id, api_key.id, trades))
            if not next_cursor or trades[-1].time < cutoff:
                break
            cursor = next_cursor

        return collected

    async def _sync_symbol_scan(self, repo: TradeRepository, api_key: ApiKey, client: BaseExchangeClient, market_type: MarketType, cutoff: datetime, full: bool = False) -> list[NormalizedTrade]:
        exchange = api_key.exchange
        if not self.symbol_cache.has(exchange, market_type):
            await self.symbol_cache.wait_for(exchange, market_type)

        universe = self.symbol_cache.get(exchange, market_type)
        if not universe:
            logger.warning(f"[{exchange.value}] no cached symbols for {market_type.value}")
            return []

        held = await client.fetch_scan_symbols(market_type, universe)
        symbols = (list(held) + [s for s in universe if s not in set(held)]) if full else held
        if not symbols:
            logger.info(f"[{exchange.value}] {market_type.value}: no symbols with balance to scan")
            return []
        scope = f"{len(held)} with balance + {len(symbols) - len(held)} more" if full else f"{len(held)} with balance"
        logger.info(f"[{exchange.value}] {market_type.value}: scanning {scope}")

        start_ms = int(cutoff.timestamp() * 1000)
        sem = asyncio.Semaphore(self._CONCURRENCY)
        write_lock = asyncio.Lock()
        collected: list[NormalizedTrade] = []

        async def _scan(sym):
            async with sem:
                try:
                    trades = await client.fetch_trades_by_symbol(market_type, sym, start_ms=start_ms)
                    if not trades:
                        return

                    while len(trades) >= self._PAGE_FULL:
                        more = await client.fetch_trades_by_symbol(market_type, sym, since_id=trades[-1].id)
                        if not more:
                            break
                        trades.extend(more)
                except FETCH_ERRORS as e:
                    logger.warning(f"[{exchange.value}] {market_type.value}/{sym}: scan failed: {e}")
                    return

                async with write_lock:
                    collected.extend(await repo.upsert_many(api_key.user_id, api_key.id, trades))

        await asyncio.gather(*[_scan(s) for s in symbols])
        logger.info(f"[{exchange.value}] {market_type.value}: {len(symbols)} symbols scanned, {len(collected)} new trades")
        return collected
