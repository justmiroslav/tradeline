import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, func, and_, update, text
from sqlalchemy.dialects.postgresql import insert

from db.repositories.base import BaseRepository
from domain.enums import Exchange, MarketType
from domain.models import MarketKline, MarketSetup, MarketUniverse

_LINK_SETUPS = """
UPDATE positions p
SET setup = ms.setup
FROM market_setups ms
WHERE p.setup IS NULL
  AND ms.exchange = p.exchange
  AND ms.market_type = p.market_type
  AND ms.symbol = p.symbol
  AND ms.time = date_bin('15 minutes', p.opened_at, TIMESTAMPTZ 'epoch') - INTERVAL '15 minutes'
"""

class MarketRepository(BaseRepository):
    async def activate(self, exchange: Exchange, symbols: list[tuple[MarketType, str]]) -> None:
        if not symbols:
            return
        rows = [{"exchange": exchange, "market_type": mt, "symbol": sym} for mt, sym in symbols]
        await self.session.execute(
            insert(MarketUniverse).values(rows).on_conflict_do_nothing(
                index_elements=["exchange", "market_type", "symbol"]
            )
        )
        await self.session.commit()

    async def list_universe(self) -> Sequence[MarketUniverse]:
        r = await self.session.execute(select(MarketUniverse))
        return r.scalars().all()

    async def insert_klines(self, rows: list[dict]) -> None:
        if not rows:
            return
        for batch in self.batches(rows):
            await self.session.execute(
                insert(MarketKline).values(batch).on_conflict_do_nothing(
                    index_elements=["exchange", "market_type", "symbol", "time"]
                )
            )
        await self.session.commit()

    async def klines_since(self, exchange: Exchange, market_type: MarketType, symbol: str, since: Optional[datetime]) -> Sequence[MarketKline]:
        stmt = select(MarketKline).where(and_(
            MarketKline.exchange == exchange, MarketKline.market_type == market_type, MarketKline.symbol == symbol
        ))
        if since is not None:
            stmt = stmt.where(MarketKline.time >= since)
        r = await self.session.execute(stmt.order_by(MarketKline.time))
        return r.scalars().all()

    async def klines_between(self, exchange: Exchange, market_type: MarketType, symbol: str, start: datetime, end: datetime) -> Sequence[MarketKline]:
        r = await self.session.execute(
            select(MarketKline).where(and_(
                MarketKline.exchange == exchange, MarketKline.market_type == market_type,
                MarketKline.symbol == symbol, MarketKline.time >= start, MarketKline.time <= end
            )).order_by(MarketKline.time)
        )
        return r.scalars().all()

    async def max_setup_time(self, exchange: Exchange, market_type: MarketType, symbol: str) -> Optional[datetime]:
        r = await self.session.execute(
            select(func.max(MarketSetup.time)).where(and_(
                MarketSetup.exchange == exchange, MarketSetup.market_type == market_type, MarketSetup.symbol == symbol
            ))
        )
        return r.scalar_one_or_none()

    async def upsert_setups(self, rows: list[dict]) -> None:
        if not rows:
            return
        for batch in self.batches(rows):
            stmt = insert(MarketSetup).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["exchange", "market_type", "symbol", "time"],
                set_={"setup": stmt.excluded.setup, "context": stmt.excluded.context, "computed_at": func.now()}
            )
            await self.session.execute(stmt)
        await self.session.commit()

    async def touch_universe(self, exchange: Exchange, market_type: MarketType, symbol: str, when: datetime) -> None:
        await self.session.execute(
            update(MarketUniverse).where(and_(
                MarketUniverse.exchange == exchange, MarketUniverse.market_type == market_type, MarketUniverse.symbol == symbol
            )).values(last_klines_at=when)
        )
        await self.session.commit()

    async def link_position_setups(self, user_id: Optional[uuid.UUID] = None) -> list[uuid.UUID]:
        sql = _LINK_SETUPS
        params: dict = {}
        if user_id is not None:
            sql = f"{sql}  AND p.user_id = :uid"
            params["uid"] = user_id
        sql = f"{sql}\nRETURNING p.user_id"
        result = await self.session.execute(text(sql), params)
        user_ids = list({row[0] for row in result.fetchall()})
        await self.session.commit()
        return user_ids
