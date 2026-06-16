from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from domain.models import Position
from features.analytics.schemas import (
    AnalyticsOut, AveragingStat, BucketStat, DailyPnl, DurationStat, EquityPoint,
    ExcursionStat, KpiOut, OpenExposure
)

REPLAY_MARGIN = timedelta(seconds=120)
_ZERO = Decimal(0)

def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2

def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None

class _Bucket:
    __slots__ = ("net", "count", "wins", "volume")

    def __init__(self):
        self.net = _ZERO
        self.count = 0
        self.wins = 0
        self.volume = _ZERO

    def add(self, net: Decimal, is_win: bool, volume: Decimal) -> None:
        self.net += net
        self.count += 1
        self.wins += 1 if is_win else 0
        self.volume += volume

    def stat(self, key: str) -> BucketStat:
        return BucketStat(
            key=key,
            net_pnl=str(self.net),
            count=self.count,
            win_rate=self.wins / self.count if self.count else 0.0,
            avg_pnl=str(self.net / self.count) if self.count else "0",
            volume=str(self.volume)
        )

class OverviewAccumulator:
    def __init__(self):
        self.watermark: datetime | None = None
        self.boundary: dict[UUID, datetime] = {}
        self.net_total = _ZERO
        self.gross_profit = _ZERO
        self.gross_loss = _ZERO
        self.wins = 0
        self.count = 0
        self.total_trades = 0
        self.total_volume = _ZERO
        self.total_fees = _ZERO
        self.largest_win = _ZERO
        self.largest_loss = _ZERO
        self.cumulative = _ZERO
        self.peak = _ZERO
        self.max_drawdown = _ZERO
        self.win_streak = 0
        self.loss_streak = 0
        self.cur_win = 0
        self.cur_loss = 0
        self.by_symbol: dict[str, _Bucket] = {}
        self.by_setup: dict[str, _Bucket] = {}
        self.by_side: dict[str, _Bucket] = {}
        self.by_market: dict[str, _Bucket] = {}
        self.by_hour: dict[str, _Bucket] = {}
        self.by_weekday: dict[str, _Bucket] = {}
        self.daily: dict[str, list] = {}
        self.equity: list[tuple[str, str]] = []
        self.win_durations: list[float] = []
        self.loss_durations: list[float] = []
        self.ad_count = 0
        self.ad_wins = 0
        self.ad_net = _ZERO
        self.rest_count = 0
        self.rest_wins = 0
        self.rest_net = _ZERO
        self.mfe_values: list[float] = []
        self.mae_values: list[float] = []
        self.winner_mfe: list[float] = []
        self.loser_mae: list[float] = []

    def extend(self, positions: Sequence[Position]) -> bool:
        fresh = [p for p in positions if p.closed_at is not None and p.id not in self.boundary]
        if self.watermark is not None and any(p.closed_at < self.watermark for p in fresh if p.closed_at is not None):
            return False
        for p in fresh:
            self.add(p)
        return True

    def add(self, p: Position) -> None:
        if p.closed_at is None:
            return
        closed_at = p.closed_at
        net = p.realized_pnl - p.fees_quote
        volume = p.entry_notional
        is_win = net > _ZERO

        self._count_outcome(net, is_win)
        self._track_equity(closed_at, net)
        self._fill_buckets(p, closed_at, net, is_win, volume)
        self._track_duration(p, closed_at, is_win)
        self._track_averaging(p, net, is_win)
        self._track_excursion(p, is_win)
        self.total_trades += p.trade_count
        self.total_volume += volume
        self.total_fees += p.fees_quote
        self._advance(p.id, closed_at)

    def result(self, open_positions: Sequence[Position], incomplete_count: int = 0) -> AnalyticsOut:
        return AnalyticsOut(
            incomplete_count=incomplete_count,
            kpis=self._kpis(),
            by_symbol=self._stats(self.by_symbol, by_net=True),
            by_setup=self._stats(self.by_setup, by_net=True),
            by_side=self._stats(self.by_side, by_net=True),
            by_market=self._stats(self.by_market, by_net=True),
            by_hour=self._stats(self.by_hour, by_net=False),
            by_weekday=self._stats(self.by_weekday, by_net=False),
            daily_pnl=[DailyPnl(date=day, net_pnl=str(v[0]), count=v[1]) for day, v in sorted(self.daily.items())],
            equity_curve=[EquityPoint(time=t, equity=e) for t, e in self.equity],
            duration=self._duration(),
            averaging=self._averaging(),
            excursion=self._excursion(),
            open_exposure=self._exposure(open_positions)
        )

    def _count_outcome(self, net: Decimal, is_win: bool) -> None:
        self.net_total += net
        self.count += 1
        if is_win:
            self.wins += 1
            self.gross_profit += net
            self.largest_win = max(self.largest_win, net)
            self.cur_win += 1
            self.cur_loss = 0
            self.win_streak = max(self.win_streak, self.cur_win)
        else:
            self.gross_loss += -net
            self.largest_loss = min(self.largest_loss, net)
            self.cur_loss += 1
            self.cur_win = 0
            self.loss_streak = max(self.loss_streak, self.cur_loss)

    def _track_equity(self, closed_at: datetime, net: Decimal) -> None:
        self.cumulative += net
        self.equity.append((closed_at.isoformat(), str(self.cumulative)))
        self.peak = max(self.peak, self.cumulative)
        self.max_drawdown = max(self.max_drawdown, self.peak - self.cumulative)

    def _fill_buckets(self, p: Position, closed_at: datetime, net: Decimal, is_win: bool, volume: Decimal) -> None:
        self._bucket(self.by_symbol, p.symbol).add(net, is_win, volume)
        self._bucket(self.by_setup, p.setup or "unlabeled").add(net, is_win, volume)
        self._bucket(self.by_side, p.side.value).add(net, is_win, volume)
        self._bucket(self.by_market, p.market_type.value).add(net, is_win, volume)
        self._bucket(self.by_hour, str(closed_at.hour)).add(net, is_win, volume)
        self._bucket(self.by_weekday, str(closed_at.weekday())).add(net, is_win, volume)
        day_entry = self.daily.setdefault(closed_at.date().isoformat(), [_ZERO, 0])
        day_entry[0] += net
        day_entry[1] += 1

    def _track_duration(self, p: Position, closed_at: datetime, is_win: bool) -> None:
        minutes = (closed_at - p.opened_at).total_seconds() / 60
        (self.win_durations if is_win else self.loss_durations).append(minutes)

    def _track_averaging(self, p: Position, net: Decimal, is_win: bool) -> None:
        if p.averaged_down:
            self.ad_count += 1
            self.ad_net += net
            self.ad_wins += 1 if is_win else 0
        else:
            self.rest_count += 1
            self.rest_net += net
            self.rest_wins += 1 if is_win else 0

    def _track_excursion(self, p: Position, is_win: bool) -> None:
        if p.mfe is not None:
            self.mfe_values.append(float(p.mfe))
            if is_win:
                self.winner_mfe.append(float(p.mfe))
        if p.mae is not None:
            self.mae_values.append(float(p.mae))
            if not is_win:
                self.loser_mae.append(float(p.mae))

    def _advance(self, position_id: UUID, closed_at: datetime) -> None:
        if self.watermark is None or closed_at > self.watermark:
            self.watermark = closed_at
        margin_start = self.watermark - REPLAY_MARGIN
        self.boundary[position_id] = closed_at
        self.boundary = {pid: ts for pid, ts in self.boundary.items() if ts >= margin_start}

    def _kpis(self) -> KpiOut:
        losses = self.count - self.wins
        return KpiOut(
            net_pnl=str(self.net_total),
            win_rate=self.wins / self.count if self.count else 0.0,
            profit_factor=float(self.gross_profit / self.gross_loss) if self.gross_loss > _ZERO else None,
            expectancy=str(self.net_total / self.count) if self.count else "0",
            avg_win=str(self.gross_profit / self.wins) if self.wins else "0",
            avg_loss=str(-self.gross_loss / losses) if losses else "0",
            total_positions=self.count,
            total_trades=self.total_trades,
            total_volume=str(self.total_volume),
            total_fees=str(self.total_fees),
            largest_win=str(self.largest_win),
            largest_loss=str(self.largest_loss),
            max_drawdown=str(self.max_drawdown),
            win_streak=self.win_streak,
            loss_streak=self.loss_streak
        )

    def _duration(self) -> DurationStat:
        return DurationStat(
            avg_win_minutes=_mean(self.win_durations),
            avg_loss_minutes=_mean(self.loss_durations),
            median_win_minutes=_median(self.win_durations),
            median_loss_minutes=_median(self.loss_durations)
        )

    def _averaging(self) -> AveragingStat:
        return AveragingStat(
            averaged_down_count=self.ad_count,
            averaged_down_net=str(self.ad_net),
            averaged_down_win_rate=self.ad_wins / self.ad_count if self.ad_count else 0.0,
            rest_count=self.rest_count,
            rest_net=str(self.rest_net),
            rest_win_rate=self.rest_wins / self.rest_count if self.rest_count else 0.0
        )

    def _excursion(self) -> ExcursionStat:
        return ExcursionStat(
            avg_mfe=_mean(self.mfe_values),
            avg_mae=_mean(self.mae_values),
            avg_winner_mfe=_mean(self.winner_mfe),
            avg_loser_mae=_mean(self.loser_mae)
        )

    @staticmethod
    def _exposure(open_positions: Sequence[Position]) -> OpenExposure:
        notional = sum((p.qty * p.entry_price for p in open_positions), _ZERO)
        return OpenExposure(count=len(open_positions), notional=str(notional))

    @staticmethod
    def _bucket(buckets: dict[str, _Bucket], key: str) -> _Bucket:
        bucket = buckets.get(key)
        if bucket is None:
            bucket = _Bucket()
            buckets[key] = bucket
        return bucket

    @staticmethod
    def _stats(buckets: dict[str, _Bucket], by_net: bool) -> list[BucketStat]:
        stats = [b.stat(key) for key, b in buckets.items()]
        if by_net:
            stats.sort(key=lambda s: Decimal(s.net_pnl), reverse=True)
        else:
            stats.sort(key=lambda s: int(s.key))
        return stats

def compute_overview(closed: Sequence[Position], open_positions: Sequence[Position]) -> AnalyticsOut:
    accumulator = OverviewAccumulator()
    for p in closed:
        accumulator.add(p)
    return accumulator.result(open_positions)
