from pydantic import BaseModel

class KpiOut(BaseModel):
    net_pnl: str
    win_rate: float
    profit_factor: float | None
    expectancy: str
    avg_win: str
    avg_loss: str
    total_positions: int
    total_trades: int
    total_volume: str
    total_fees: str
    largest_win: str
    largest_loss: str
    max_drawdown: str
    win_streak: int
    loss_streak: int

class BucketStat(BaseModel):
    key: str
    net_pnl: str
    count: int
    win_rate: float
    avg_pnl: str
    volume: str

class DailyPnl(BaseModel):
    date: str
    net_pnl: str
    count: int

class EquityPoint(BaseModel):
    time: str
    equity: str

class DurationStat(BaseModel):
    avg_win_minutes: float | None
    avg_loss_minutes: float | None
    median_win_minutes: float | None
    median_loss_minutes: float | None

class OpenExposure(BaseModel):
    count: int
    notional: str

class AveragingStat(BaseModel):
    averaged_down_count: int
    averaged_down_net: str
    averaged_down_win_rate: float
    rest_count: int
    rest_net: str
    rest_win_rate: float

class ExcursionStat(BaseModel):
    avg_mfe: float | None
    avg_mae: float | None
    avg_winner_mfe: float | None
    avg_loser_mae: float | None

class AnalyticsOut(BaseModel):
    kpis: KpiOut
    by_symbol: list[BucketStat]
    by_setup: list[BucketStat]
    by_side: list[BucketStat]
    by_market: list[BucketStat]
    by_hour: list[BucketStat]
    by_weekday: list[BucketStat]
    daily_pnl: list[DailyPnl]
    equity_curve: list[EquityPoint]
    duration: DurationStat
    averaging: AveragingStat
    excursion: ExcursionStat
    open_exposure: OpenExposure
    incomplete_count: int = 0
