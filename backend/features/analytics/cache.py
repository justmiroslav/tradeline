import asyncio

from dataclasses import dataclass, field
from uuid import UUID

from domain.filters import AnalyticsFilters
from features.analytics.compute import OverviewAccumulator
from features.analytics.schemas import AnalyticsOut

@dataclass(slots=True)
class CacheEntry:
    accumulator: OverviewAccumulator
    out: AnalyticsOut
    version: int

@dataclass(slots=True)
class _UserState:
    version: int = 0
    invalidate_version: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

class AnalyticsCache:
    _MAX_ENTRIES = 128

    def __init__(self):
        self._users: dict[UUID, _UserState] = {}
        self._entries: dict[tuple[UUID, AnalyticsFilters], CacheEntry] = {}

    def bump_append(self, user_id: UUID) -> None:
        self._state(user_id).version += 1

    def bump_invalidate(self, user_id: UUID) -> None:
        state = self._state(user_id)
        state.version += 1
        state.invalidate_version = state.version

    def version(self, user_id: UUID) -> int:
        return self._state(user_id).version

    def invalidate_version(self, user_id: UUID) -> int:
        return self._state(user_id).invalidate_version

    def lock(self, user_id: UUID) -> asyncio.Lock:
        return self._state(user_id).lock

    def get(self, user_id: UUID, filters: AnalyticsFilters) -> CacheEntry | None:
        key = (user_id, filters)
        entry = self._entries.pop(key, None)
        if entry is None:
            return None
        self._entries[key] = entry
        return entry

    def put(self, user_id: UUID, filters: AnalyticsFilters, entry: CacheEntry) -> None:
        key = (user_id, filters)
        self._entries.pop(key, None)
        if len(self._entries) >= self._MAX_ENTRIES:
            self._entries.pop(next(iter(self._entries)))
        self._entries[key] = entry

    def _state(self, user_id: UUID) -> _UserState:
        state = self._users.get(user_id)
        if state is None:
            state = _UserState()
            self._users[user_id] = state
        return state
