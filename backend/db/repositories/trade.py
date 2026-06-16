import uuid
from datetime import datetime
from typing import AsyncIterator, Optional, Sequence

from sqlalchemy import select, func, or_, update, and_
from sqlalchemy.dialects.postgresql import insert

from db.mappers import normalized_trade_to_row
from db.repositories.base import BaseRepository
from db.repositories.filtering import apply_filters
from domain.enums import MarketType
from domain.filters import AnalyticsFilters
from domain.models import Position, Trade
from exchanges.types import NormalizedTrade

class TradeRepository(BaseRepository):
    @staticmethod
    def _position_id():
        return (
            select(Position.id)
            .where(
                Position.api_key_id == Trade.api_key_id,
                Position.symbol == Trade.symbol,
                Position.opened_at <= Trade.time,
                or_(Position.closed_at.is_(None), Trade.time <= Position.closed_at)
            )
            .correlate(Trade)
            .order_by(Position.opened_at.desc())
            .limit(1)
            .scalar_subquery()
        )

    async def get_page(self, user_id: uuid.UUID, filters: AnalyticsFilters, cutoff: datetime, page: int = 1, size: int = 50) -> tuple[Sequence[Trade], int]:
        stmt = apply_filters(
            select(Trade, self._position_id().label("position_id")).where(Trade.user_id == user_id, Trade.time >= cutoff),
            Trade, filters, Trade.time
        )
        count_stmt = apply_filters(
            select(func.count()).select_from(Trade).where(Trade.user_id == user_id, Trade.time >= cutoff),
            Trade, filters, Trade.time
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        rows = (await self.session.execute(
            stmt.order_by(Trade.time.desc()).offset((page - 1) * size).limit(size)
        )).all()
        trades = []
        for trade, pid in rows:
            trade.position_id = pid
            trades.append(trade)
        return trades, total

    async def stream_for_replay(self, user_id: uuid.UUID) -> AsyncIterator[Trade]:
        result = await self.session.stream_scalars(
            select(Trade).where(Trade.user_id == user_id).order_by(Trade.time).execution_options(yield_per=500)
        )
        async for trade in result:
            yield trade

    async def max_trade_time(self, api_key_id: uuid.UUID, market_type: MarketType) -> Optional[datetime]:
        r = await self.session.execute(
            select(func.max(Trade.time)).where(
                and_(Trade.api_key_id == api_key_id, Trade.market_type == market_type)
            )
        )
        return r.scalar_one_or_none()

    async def time_range(self, user_id: uuid.UUID) -> tuple[Optional[datetime], Optional[datetime]]:
        r = await self.session.execute(
            select(func.min(Trade.time), func.max(Trade.time)).where(Trade.user_id == user_id)
        )
        row = r.one()
        return row[0], row[1]

    async def stream_filtered(self, user_id: uuid.UUID, filters: AnalyticsFilters, cutoff: datetime) -> AsyncIterator[Trade]:
        stmt = apply_filters(select(Trade).where(Trade.user_id == user_id, Trade.time >= cutoff), Trade, filters, Trade.time)
        result = await self.session.stream_scalars(
            stmt.order_by(Trade.time.desc()).execution_options(yield_per=500)
        )
        async for trade in result:
            yield trade

    async def distinct_symbols(self, api_key_id: uuid.UUID) -> list[tuple[MarketType, str]]:
        r = await self.session.execute(
            select(Trade.market_type, Trade.symbol).where(Trade.api_key_id == api_key_id).distinct()
        )
        return [(row[0], row[1]) for row in r.all()]

    async def user_symbols(self, user_id: uuid.UUID) -> list[str]:
        r = await self.session.execute(
            select(Trade.symbol).where(Trade.user_id == user_id).distinct().order_by(Trade.symbol)
        )
        return list(r.scalars().all())

    async def reassign(self, old_api_key_id: uuid.UUID, new_api_key_id: uuid.UUID, markets: list[MarketType]) -> None:
        if not markets:
            return
        await self.session.execute(
            update(Trade)
            .where(and_(Trade.api_key_id == old_api_key_id, Trade.market_type.in_(markets)))
            .values(api_key_id=new_api_key_id)
        )

    async def upsert_many(self, user_id: uuid.UUID, api_key_id: uuid.UUID, trades: list[NormalizedTrade]) -> list[NormalizedTrade]:
        if not trades:
            return []

        rows = [normalized_trade_to_row(user_id, api_key_id, t) for t in trades]
        inserted: set = set()
        for batch in self.batches(rows):
            stmt = (
                insert(Trade)
                .values(batch)
                .on_conflict_do_nothing(constraint="uq_trade_exchange_id")
                .returning(Trade.trade_id, Trade.exchange, Trade.market_type)
            )
            result = await self.session.execute(stmt)
            inserted.update((r.trade_id, r.exchange, r.market_type) for r in result)
        await self.session.commit()
        out: list[NormalizedTrade] = []
        seen: set = set()
        for t in trades:
            key = (t.id, t.exchange, t.market_type)
            if key in inserted and key not in seen:
                seen.add(key)
                out.append(t)
        return out
