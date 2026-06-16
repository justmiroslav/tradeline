import asyncio

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.repositories.trade import TradeRepository
from exchanges.types import NormalizedTrade
from features.positions.service import PositionsService
from shared.event_bus import EventBus
from utils.logger import brief, logger

class TradeIngester:
    _FLUSH_COUNT = 25
    _FLUSH_INTERVAL = 1.0
    _LIVE_SKEW_LIMIT = timedelta(seconds=60)

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], bus: EventBus,
                 on_live_change: Callable[[UUID], None], on_history_change: Callable[[UUID], None]):
        self._sf = session_factory
        self._bus = bus
        self._on_live_change = on_live_change
        self._on_history_change = on_history_change
        self._buffers: dict[UUID, tuple[UUID, list[NormalizedTrade]]] = {}
        self._backfilling: set[UUID] = set()
        self._rebuild_locks: dict[UUID, asyncio.Lock] = {}
        self._buf_lock = asyncio.Lock()
        self._task = None
        self._stopped = False

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stopped = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._flush_all()

    async def add(self, user_id: UUID, api_key_id: UUID, trade: NormalizedTrade) -> None:
        async with self._buf_lock:
            if api_key_id not in self._buffers:
                self._buffers[api_key_id] = (user_id, [])
            self._buffers[api_key_id][1].append(trade)
            ready = len(self._buffers[api_key_id][1]) >= self._FLUSH_COUNT
        if ready:
            await self._flush(api_key_id)

    def begin_backfill(self, api_key_id: UUID) -> None:
        self._backfilling.add(api_key_id)

    def end_backfill(self, api_key_id: UUID) -> None:
        self._backfilling.discard(api_key_id)

    def forget(self, api_key_id: UUID) -> None:
        self._buffers.pop(api_key_id, None)
        self._backfilling.discard(api_key_id)

    async def rebuild(self, user_id: UUID) -> None:
        async with self._lock_for(user_id):
            async with self._sf() as session:
                await PositionsService(session).rebuild(user_id)
        self._on_history_change(user_id)
        logger.info(f"[TradeIngester] positions rebuilt for user={user_id}")

    async def apply_live(self, user_id: UUID, api_key_id: UUID, trades: list[NormalizedTrade]) -> None:
        await self._apply(user_id, api_key_id, trades)
        if self._is_backdated(trades):
            self._on_history_change(user_id)
        else:
            self._on_live_change(user_id)

    async def apply_backfill(self, user_id: UUID, api_key_id: UUID, trades: list[NormalizedTrade]) -> None:
        await self._apply(user_id, api_key_id, trades)
        self._on_history_change(user_id)
        logger.info(f"[TradeIngester] {len(trades)} backfill trades applied (key={api_key_id})")

    def touch(self, user_id: UUID) -> None:
        self._on_history_change(user_id)

    @classmethod
    def _is_backdated(cls, trades: list[NormalizedTrade]) -> bool:
        now = datetime.now(timezone.utc)
        return any(now - t.time > cls._LIVE_SKEW_LIMIT for t in trades)

    def notify_synced(self, user_id: UUID, api_key_id: UUID) -> None:
        self._bus.publish(user_id, "sync", {"api_key_id": str(api_key_id), "state": "done"})

    async def _apply(self, user_id: UUID, api_key_id: UUID, trades: list[NormalizedTrade]) -> None:
        async with self._lock_for(user_id):
            async with self._sf() as session:
                await PositionsService(session).apply_incremental(user_id, api_key_id, trades)

    def _lock_for(self, user_id: UUID) -> asyncio.Lock:
        lock = self._rebuild_locks.get(user_id)
        if lock is None:
            lock = asyncio.Lock()
            self._rebuild_locks[user_id] = lock
        return lock

    async def _loop(self) -> None:
        while not self._stopped:
            await asyncio.sleep(self._FLUSH_INTERVAL)
            try:
                await self._flush_all()
            except Exception as e:
                logger.warning(f"[TradeIngester] flush error: {brief(e)}")

    async def _flush_all(self) -> None:
        for api_key_id in list(self._buffers):
            try:
                await self._flush(api_key_id)
            except Exception as e:
                logger.warning(f"[TradeIngester] flush {api_key_id} failed: {brief(e)}")

    async def _flush(self, api_key_id: UUID) -> None:
        if api_key_id in self._backfilling:
            return
        async with self._buf_lock:
            entry = self._buffers.pop(api_key_id, None)
        if entry is None:
            return
        user_id, trades = entry
        if not trades:
            return

        async with self._sf() as session:
            inserted = await TradeRepository(session).upsert_many(user_id, api_key_id, trades)

        if inserted:
            await self.apply_live(user_id, api_key_id, inserted)
            logger.info(f"[TradeIngester] {len(inserted)} live trades applied (key={api_key_id})")
            for trade in inserted:
                self._bus.publish(user_id, "trade", trade.to_payload())
