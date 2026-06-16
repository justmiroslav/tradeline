from datetime import datetime, timezone
from decimal import Decimal as D
from uuid import uuid4

from domain.enums import Exchange, MarketType, PositionSide, PositionStatus
from domain.filters import AnalyticsFilters
from domain.models import Position
from features.analytics.cache import AnalyticsCache, CacheEntry
from features.analytics.compute import OverviewAccumulator

def _pos(pnl, fee, symbol, day, hour):
    return Position(
        id=uuid4(), realized_pnl=D(pnl), fees_quote=D(fee), qty=D(1), entry_price=D(100), entry_notional=D(100),
        exchange=Exchange.BINANCE, market_type=MarketType.SPOT, symbol=symbol, setup=None,
        side=PositionSide.LONG, status=PositionStatus.CLOSED, trade_count=1,
        opened_at=datetime(2026, 4, day, hour - 1, tzinfo=timezone.utc),
        closed_at=datetime(2026, 4, day, hour, tzinfo=timezone.utc),
        averaged_down=False, mfe=None, mae=None
    )

_HISTORY = [
    _pos("100", "10", "BTC", 1, 10),
    _pos("-50", "5", "ETH", 1, 12),
    _pos("20", "2", "BTC", 2, 14),
    _pos("70", "7", "SOL", 3, 9),
    _pos("-15", "1", "ETH", 3, 18)
]

class TestIncrementalFold:
    def test_folding_new_closes_equals_full_recompute(self):
        full = OverviewAccumulator()
        full.extend(_HISTORY)

        folded = OverviewAccumulator()
        folded.extend(_HISTORY[:3])
        folded.extend(_HISTORY[3:])

        assert full.result([]) == folded.result([])

    def test_result_does_not_mutate_state(self):
        accumulator = OverviewAccumulator()
        accumulator.extend(_HISTORY)
        assert accumulator.result([]) == accumulator.result([])

    def test_open_positions_do_not_pollute_the_accumulator(self):
        accumulator = OverviewAccumulator()
        accumulator.extend(_HISTORY)
        opened = _pos("0", "0", "BTC", 4, 10)
        opened.status = PositionStatus.OPEN
        with_open = accumulator.result([opened])
        assert with_open.open_exposure.count == 1
        assert accumulator.result([]).kpis == with_open.kpis

class TestExtendGuards:
    def test_already_folded_position_is_not_double_counted(self):
        first, second = _HISTORY[0], _HISTORY[1]
        accumulator = OverviewAccumulator()
        accumulator.extend([first])
        accumulator.extend([first, second])
        assert accumulator.count == 2

    def test_same_timestamp_closes_are_deduplicated_not_dropped(self):
        one = _pos("10", "0", "BTC", 5, 10)
        twin = _pos("10", "0", "ETH", 5, 10)
        accumulator = OverviewAccumulator()
        accumulator.extend([one])
        accumulator.extend([one, twin])
        assert accumulator.count == 2

    def test_backdated_close_rejects_the_fold(self):
        accumulator = OverviewAccumulator()
        accumulator.extend([_HISTORY[1]])
        assert accumulator.extend([_HISTORY[0]]) is False
        assert accumulator.count == 1

    def test_rejected_fold_does_not_mutate_state(self):
        accumulator = OverviewAccumulator()
        accumulator.extend([_HISTORY[1]])
        before = accumulator.result([])
        accumulator.extend([_HISTORY[0], _HISTORY[2]])
        assert accumulator.result([]) == before

    def test_watermark_advances_and_never_regresses(self):
        accumulator = OverviewAccumulator()
        accumulator.extend([_HISTORY[0]])
        first_mark = accumulator.watermark
        accumulator.extend([_HISTORY[1]])
        assert first_mark is not None
        assert accumulator.watermark == _HISTORY[1].closed_at
        assert accumulator.watermark > first_mark

class TestCacheVersioning:
    def test_append_keeps_entries_delta_foldable(self):
        cache = AnalyticsCache()
        uid = uuid4()
        entry_version = cache.version(uid)
        cache.bump_append(uid)
        cache.bump_append(uid)
        assert cache.version(uid) == entry_version + 2
        assert entry_version >= cache.invalidate_version(uid)

    def test_invalidate_forces_full_rebuild(self):
        cache = AnalyticsCache()
        uid = uuid4()
        cache.bump_append(uid)
        entry_version = cache.version(uid)
        cache.bump_invalidate(uid)
        assert cache.invalidate_version(uid) == cache.version(uid)
        assert entry_version < cache.invalidate_version(uid)

    def test_distinct_users_are_independent(self):
        cache = AnalyticsCache()
        a, b = uuid4(), uuid4()
        cache.bump_invalidate(a)
        assert cache.version(b) == 0

    def test_users_have_independent_locks(self):
        cache = AnalyticsCache()
        assert cache.lock(uuid4()) is not cache.lock(uuid4())

    def test_entries_are_keyed_by_filters(self):
        cache = AnalyticsCache()
        uid = uuid4()
        everything = AnalyticsFilters()
        btc_only = AnalyticsFilters(symbols=("BTCUSDT",))
        accumulator = OverviewAccumulator()
        cache.put(uid, everything, CacheEntry(accumulator, accumulator.result([]), 0))
        assert cache.get(uid, everything) is not None
        assert cache.get(uid, btc_only) is None

    def test_lru_evicts_oldest_entry_at_capacity(self):
        cache = AnalyticsCache()
        uid = uuid4()
        accumulator = OverviewAccumulator()
        out = accumulator.result([])
        first = AnalyticsFilters(symbols=("S0",))
        cache.put(uid, first, CacheEntry(accumulator, out, 0))
        for i in range(1, AnalyticsCache._MAX_ENTRIES + 1):
            cache.put(uid, AnalyticsFilters(symbols=(f"S{i}",)), CacheEntry(accumulator, out, 0))
        assert cache.get(uid, first) is None

    def test_recently_read_entry_survives_eviction(self):
        cache = AnalyticsCache()
        uid = uuid4()
        accumulator = OverviewAccumulator()
        out = accumulator.result([])
        first = AnalyticsFilters(symbols=("S0",))
        cache.put(uid, first, CacheEntry(accumulator, out, 0))
        for i in range(1, AnalyticsCache._MAX_ENTRIES - 1):
            cache.put(uid, AnalyticsFilters(symbols=(f"S{i}",)), CacheEntry(accumulator, out, 0))
        cache.get(uid, first)
        cache.put(uid, AnalyticsFilters(symbols=("X1",)), CacheEntry(accumulator, out, 0))
        cache.put(uid, AnalyticsFilters(symbols=("X2",)), CacheEntry(accumulator, out, 0))
        assert cache.get(uid, first) is not None
