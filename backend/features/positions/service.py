from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.positions import PositionsRepository
from db.repositories.trade import TradeRepository
from domain.enums import PositionStatus
from domain.models import Trade
from exchanges.types import NormalizedTrade
from features.positions.engine import PositionsEngine, TradeEvent
from features.positions.reconcile import reconcile_open_spot

def _from_row(trade: Trade) -> TradeEvent:
    return TradeEvent(
        user_id=trade.user_id, api_key_id=trade.api_key_id,
        exchange=trade.exchange, market_type=trade.market_type, symbol=trade.symbol,
        side=trade.side, price=trade.price, quantity=trade.quantity, fee=trade.fee,
        realized_pnl=trade.realized_pnl, time=trade.time, trade_id=trade.trade_id
    )

def _from_normalized(user_id: UUID, api_key_id: UUID, nt: NormalizedTrade) -> TradeEvent:
    return TradeEvent(
        user_id=user_id, api_key_id=api_key_id,
        exchange=nt.exchange, market_type=nt.market_type, symbol=nt.symbol,
        side=nt.side, price=nt.price, quantity=nt.quantity, fee=nt.fee,
        realized_pnl=nt.realized_pnl, time=nt.time, trade_id=nt.id
    )

class PositionsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def rebuild(self, user_id: UUID) -> None:
        positions_repo = PositionsRepository(self.session)
        await positions_repo.delete_for_user(user_id)

        engine = PositionsEngine(positions_repo)
        async for trade in TradeRepository(self.session).stream_for_replay(user_id):
            await engine.apply(_from_row(trade))

        await self.session.commit()

    async def apply_incremental(self, user_id: UUID, api_key_id: UUID, trades: list[NormalizedTrade]) -> None:
        engine = PositionsEngine(PositionsRepository(self.session))
        for nt in sorted(trades, key=lambda t: t.time):
            await engine.apply(_from_normalized(user_id, api_key_id, nt))
        await self.session.commit()

    async def reconcile_incomplete(self, api_key_id: UUID, balances: dict) -> int:
        repo = PositionsRepository(self.session)
        positions = await repo.open_spot_for_key(api_key_id)
        created = reconcile_open_spot(positions, balances)
        for inc in created:
            repo.add(inc)
        await self.session.commit()
        whole = sum(1 for p in positions if p.status == PositionStatus.INCOMPLETE)
        return whole + len(created)
