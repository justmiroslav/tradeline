import asyncio, multiprocessing

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.repositories.market import MarketRepository
from db.repositories.positions import PositionsRepository
from domain.enums import PositionSide
from domain.models import MarketKline, MarketUniverse, Position
from domain.plans import market_history_months
from exchanges.gateway import ExchangeGateway
from exchanges.helpers import FETCH_ERRORS
from exchanges.types import Kline
from features.analytics.cache import AnalyticsCache
from features.market_setups.classifier import LOOKBACK_BARS, classify_rows
from shared.exceptions import ExchangeError
from shared.worker import PeriodicWorker
from utils.logger import brief, logger

_BAR = timedelta(minutes=15)
_BAR_MS = 15 * 60 * 1000
_BACKFILL_HEADROOM_DAYS = 1
_EXCURSION_WINDOW = timedelta(days=120)

def _to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)

def _to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

def _floor_bar(dt: datetime) -> datetime:
    return _to_dt((_to_ms(dt) // _BAR_MS) * _BAR_MS)

def _mp_context():
    try:
        return multiprocessing.get_context("forkserver")
    except ValueError:
        return multiprocessing.get_context()

def _to_domain(row: MarketKline) -> Kline:
    return Kline(time_ms=_to_ms(row.time), open=row.open, high=row.high, low=row.low, close=row.close, volume=row.volume)

def _excursion(position: Position, klines: list[MarketKline]) -> tuple[Optional[Decimal], Optional[Decimal]]:
    entry = position.entry_price
    if entry <= 0 or not klines:
        return None, None
    zero = Decimal(0)
    high = max(k.high for k in klines)
    low = min(k.low for k in klines)
    if position.side == PositionSide.LONG:
        return max(zero, (high - entry) / entry), max(zero, (entry - low) / entry)
    return max(zero, (entry - low) / entry), max(zero, (high - entry) / entry)

class MarketSetupWorker(PeriodicWorker):
    _TICK_SECONDS = 60
    _FIRST_DELAY = 25
    _LABEL = "MarketSetupWorker"
    _PER_EXCHANGE_CONCURRENCY = 3
    _BACKFILL_BATCH = 3
    _CLASSIFY_WORKERS = 2

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], gateway: ExchangeGateway, analytics_cache: AnalyticsCache):
        super().__init__()
        self._sf = session_factory
        self._gateway = gateway
        self._cache = analytics_cache
        self._pool: Optional[ProcessPoolExecutor] = None

    def start(self) -> None:
        self._pool = ProcessPoolExecutor(max_workers=self._CLASSIFY_WORKERS, mp_context=_mp_context())
        super().start()

    async def stop(self) -> None:
        await super().stop()
        if self._pool:
            self._pool.shutdown(wait=False, cancel_futures=True)
            self._pool = None

    def _recover_pool(self, broken: ProcessPoolExecutor) -> None:
        if self._pool is not broken:
            return
        self._pool = ProcessPoolExecutor(max_workers=self._CLASSIFY_WORKERS, mp_context=_mp_context())
        broken.shutdown(wait=False, cancel_futures=True)
        logger.warning("[MarketSetupWorker] classify pool broke — rebuilt")

    async def _tick(self) -> None:
        now = datetime.now(timezone.utc)
        now_ms = _to_ms(now)
        latest_closed_ms = (now_ms // _BAR_MS - 1) * _BAR_MS
        async with self._sf() as session:
            universe = await MarketRepository(session).list_universe()

        due = [e for e in universe if e.last_klines_at is None or _to_ms(e.last_klines_at) < latest_closed_ms]
        incremental = [e for e in due if e.last_klines_at is not None]
        backfilling = [e for e in due if e.last_klines_at is None]
        batch = incremental + backfilling[: self._BACKFILL_BATCH]
        if batch:
            sems: dict = {}
            for entry in batch:
                sems.setdefault(entry.exchange, asyncio.Semaphore(self._PER_EXCHANGE_CONCURRENCY))
            await asyncio.gather(*[self._refresh_guarded(e, sems[e.exchange], now, now_ms, latest_closed_ms) for e in batch])

        await self._enrich_positions()

    async def _enrich_positions(self) -> None:
        async with self._sf() as session:
            linked = await MarketRepository(session).link_position_setups()
        for uid in linked:
            self._cache.bump_invalidate(uid)
        await self._reconcile_excursions()

    async def _refresh_guarded(self, entry: MarketUniverse, sem: asyncio.Semaphore, now: datetime, now_ms: int, latest_closed_ms: int) -> None:
        async with sem:
            try:
                await self._refresh(entry, now, now_ms, latest_closed_ms)
            except (*FETCH_ERRORS, ExchangeError) as e:
                logger.warning(f"[MarketSetupWorker] {self._tag(entry)}: fetch failed: {brief(e)}")
            except Exception as e:
                logger.warning(f"[MarketSetupWorker] {self._tag(entry)}: error: {brief(e)}")

    async def _refresh(self, entry: MarketUniverse, now: datetime, now_ms: int, latest_closed_ms: int) -> None:
        if entry.last_klines_at is None:
            backfilling = True
            window = market_history_months(entry.exchange, entry.market_type) * 30 + _BACKFILL_HEADROOM_DAYS
            start_ms = _to_ms(now - timedelta(days=window)) - _BAR_MS * LOOKBACK_BARS
        else:
            backfilling = False
            start_ms = _to_ms(entry.last_klines_at) + _BAR_MS

        fetched = await self._gateway.fetch_klines_range(entry.exchange, entry.market_type, entry.symbol, start_ms, now_ms)
        closed = [k for k in fetched if k.time_ms <= latest_closed_ms]
        if not closed:
            if backfilling:
                logger.warning(f"[MarketSetupWorker] {self._tag(entry)}: no klines available for the backfill window")
            return

        rows = [self._kline_row(entry, k) for k in closed]
        last_bar = _to_dt(max(k.time_ms for k in closed))

        async with self._sf() as session:
            repo = MarketRepository(session)
            await repo.insert_klines(rows)
            await repo.touch_universe(entry.exchange, entry.market_type, entry.symbol, last_bar)
            last_setup = await repo.max_setup_time(entry.exchange, entry.market_type, entry.symbol)
            since = last_setup - _BAR * LOOKBACK_BARS if last_setup else None
            stored = await repo.klines_since(entry.exchange, entry.market_type, entry.symbol, since)

        if len(stored) < LOOKBACK_BARS:
            if backfilling:
                logger.warning(f"[MarketSetupWorker] {self._tag(entry)}: only {len(stored)} bars available, setups need {LOOKBACK_BARS}")
            return

        candles = [_to_domain(k) for k in stored]
        last_setup_ms = _to_ms(last_setup) if last_setup else -1
        loop = asyncio.get_running_loop()
        pool = self._pool
        try:
            setup_rows = await loop.run_in_executor(
                pool, classify_rows, entry.exchange, entry.market_type, entry.symbol, candles, last_setup_ms
            )
        except BrokenProcessPool:
            self._recover_pool(pool)
            return
        if not setup_rows:
            return

        async with self._sf() as session:
            await MarketRepository(session).upsert_setups(setup_rows)

    async def _reconcile_excursions(self) -> None:
        since = datetime.now(timezone.utc) - _EXCURSION_WINDOW
        async with self._sf() as session:
            positions = await PositionsRepository(session).needing_excursions(200, since)
        if not positions:
            return

        groups: dict = {}
        for p in positions:
            groups.setdefault((p.exchange, p.market_type, p.symbol), []).append(p)

        changed: set = set()
        for (exchange, market_type, symbol), batch in groups.items():
            ends = [p.closed_at for p in batch if p.closed_at is not None]
            if not ends:
                continue

            start = _floor_bar(min(p.opened_at for p in batch))
            async with self._sf() as session:
                klines = await MarketRepository(session).klines_between(exchange, market_type, symbol, start, max(ends))
            if not klines:
                continue

            async with self._sf() as session:
                repo = PositionsRepository(session)
                for p in batch:
                    if p.closed_at is None:
                        continue
                    window = [k for k in klines if _floor_bar(p.opened_at) <= k.time <= p.closed_at]
                    mfe, mae = _excursion(p, window)
                    if mfe is not None:
                        await repo.set_excursions(p.id, mfe, mae)
                        changed.add(p.user_id)
                await session.commit()

        for uid in changed:
            self._cache.bump_invalidate(uid)

    @staticmethod
    def _tag(entry: MarketUniverse) -> str:
        return f"{entry.exchange.value}/{entry.symbol} {entry.market_type.value}"

    @staticmethod
    def _kline_row(entry: MarketUniverse, k: Kline) -> dict:
        return {
            "exchange": entry.exchange, "market_type": entry.market_type, "symbol": entry.symbol,
            "time": _to_dt(k.time_ms),
            "open": k.open, "high": k.high, "low": k.low, "close": k.close, "volume": k.volume
        }
