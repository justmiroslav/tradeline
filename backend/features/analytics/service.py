from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.analytics import AnalyticsRepository
from domain.filters import AnalyticsFilters
from features.analytics.cache import AnalyticsCache, CacheEntry
from features.analytics.compute import OverviewAccumulator, REPLAY_MARGIN
from features.analytics.schemas import AnalyticsOut
from utils.logger import logger

class AnalyticsService:
    def __init__(self, session: AsyncSession, cache: AnalyticsCache):
        self.session = session
        self._cache = cache

    async def get_overview(self, user_id: UUID, filters: AnalyticsFilters) -> AnalyticsOut:
        cached = self._cache.get(user_id, filters)
        if cached is not None and cached.version == self._cache.version(user_id):
            return cached.out

        async with self._cache.lock(user_id):
            cached = self._cache.get(user_id, filters)
            version = self._cache.version(user_id)
            if cached is not None and cached.version == version:
                return cached.out

            repo = AnalyticsRepository(self.session)
            accumulator = await self._folded(repo, user_id, filters, cached)
            if accumulator is None:
                accumulator = await self._rebuilt(repo, user_id, filters)

            out = accumulator.result(
                await repo.open_positions(user_id, filters),
                await repo.count_incomplete(user_id)
            )
            self._cache.put(user_id, filters, CacheEntry(accumulator, out, version))
            return out

    async def _folded(self, repo: AnalyticsRepository, user_id: UUID, filters: AnalyticsFilters,
                      cached: CacheEntry | None) -> OverviewAccumulator | None:
        if cached is None or cached.version < self._cache.invalidate_version(user_id):
            return None
        accumulator = cached.accumulator
        watermark = accumulator.watermark
        if watermark is None:
            return None

        fresh = await repo.closed_positions_since(user_id, filters, watermark - REPLAY_MARGIN)
        if not accumulator.extend(fresh):
            return None

        if fresh:
            logger.info(f"[analytics] folded {len(fresh)} closed positions into cached overview (user={user_id})")
        return accumulator

    @staticmethod
    async def _rebuilt(repo: AnalyticsRepository, user_id: UUID, filters: AnalyticsFilters) -> OverviewAccumulator:
        accumulator = OverviewAccumulator()
        closed = await repo.closed_positions(user_id, filters)
        accumulator.extend(closed)
        logger.info(f"[analytics] overview rebuilt from {len(closed)} closed positions (user={user_id})")
        return accumulator
