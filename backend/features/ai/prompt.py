from functools import lru_cache
from pathlib import Path

from features.analytics.schemas import AnalyticsOut, BucketStat

_SKILL = Path(__file__).with_name("skill.md")
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

@lru_cache
def load_skill() -> str:
    return _SKILL.read_text(encoding="utf-8").strip()

def _f(value: str | None) -> float:
    try:
        return float(value) if value is not None else 0.0
    except ValueError:
        return 0.0

def _money(value: str | None) -> str:
    v = _f(value)
    return f"{'-' if v < 0 else ''}${abs(v):,.2f}"

def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"

def _optpct(value: float | None) -> str:
    return f"{value * 100:.1f}%" if value is not None else "n/a"

def _dur(minutes: float | None) -> str:
    if minutes is None:
        return "n/a"
    if minutes < 60:
        return f"{minutes:.0f}m"
    return f"{int(minutes // 60)}h {int(minutes % 60)}m"

def _weekday(key: str) -> str:
    try:
        return _WEEKDAYS[int(key)]
    except (ValueError, IndexError):
        return key

def _bucket(b: BucketStat) -> str:
    return f"{b.key} {_money(b.net_pnl)} ({b.count} pos, {_pct(b.win_rate)} win)"

def build_user_message(a: AnalyticsOut) -> str:
    k = a.kpis
    pf = f"{k.profit_factor:.2f}" if k.profit_factor is not None else "n/a (no losing positions)"
    lines = [
        f"Closed positions: {k.total_positions} | Net P&L: {_money(k.net_pnl)} | Win rate: {_pct(k.win_rate)}",
        f"Profit factor: {pf} | Expectancy/pos: {_money(k.expectancy)} | Avg win: {_money(k.avg_win)} | Avg loss: {_money(k.avg_loss)}",
        f"Max drawdown: {_money(k.max_drawdown)} | Largest win: {_money(k.largest_win)} | Largest loss: {_money(k.largest_loss)} | Longest win/loss streak: {k.win_streak}/{k.loss_streak}"
    ]

    if a.by_symbol:
        winners = [b for b in a.by_symbol if _f(b.net_pnl) > 0][:3]
        losers = [b for b in a.by_symbol if _f(b.net_pnl) < 0][-3:]
        if winners:
            lines.append("Top symbols: " + "; ".join(_bucket(b) for b in winners))
        if losers:
            lines.append("Worst symbols: " + "; ".join(_bucket(b) for b in losers))
    if a.by_setup:
        lines.append("By setup: " + "; ".join(_bucket(b) for b in a.by_setup))
    if a.by_side:
        lines.append("By side: " + "; ".join(_bucket(b) for b in a.by_side))
    if a.by_market:
        lines.append("By market: " + "; ".join(_bucket(b) for b in a.by_market))
    if a.by_hour:
        best = max(a.by_hour, key=lambda b: _f(b.net_pnl))
        worst = min(a.by_hour, key=lambda b: _f(b.net_pnl))
        lines.append(f"Best hour (UTC): {best.key}:00 {_money(best.net_pnl)} | Worst hour: {worst.key}:00 {_money(worst.net_pnl)}")
    if a.by_weekday:
        best = max(a.by_weekday, key=lambda b: _f(b.net_pnl))
        worst = min(a.by_weekday, key=lambda b: _f(b.net_pnl))
        lines.append(f"Best weekday: {_weekday(best.key)} {_money(best.net_pnl)} | Worst weekday: {_weekday(worst.key)} {_money(worst.net_pnl)}")

    d = a.duration
    lines.append(f"Avg hold — winners: {_dur(d.avg_win_minutes)}, losers: {_dur(d.avg_loss_minutes)}")
    av = a.averaging
    lines.append(
        f"Averaging down: {av.averaged_down_count} pos, {_money(av.averaged_down_net)} net, {_pct(av.averaged_down_win_rate)} win"
        f" vs rest: {av.rest_count} pos, {_money(av.rest_net)} net, {_pct(av.rest_win_rate)} win"
    )
    ex = a.excursion
    lines.append(f"Excursion — avg MFE: {_optpct(ex.avg_mfe)}, avg MAE: {_optpct(ex.avg_mae)}, winner MFE: {_optpct(ex.avg_winner_mfe)}, loser MAE: {_optpct(ex.avg_loser_mae)}")

    return "\n".join(lines)
