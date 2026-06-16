from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from db.repositories.positions import PositionsRepository
from domain.enums import Exchange, MarketType, PositionSide, PositionStatus, TradeSide
from domain.models import Position
from utils.logger import logger

_D0 = Decimal(0)

@dataclass(frozen=True, slots=True)
class TradeEvent:
    user_id: UUID
    api_key_id: UUID
    exchange: Exchange
    market_type: MarketType
    symbol: str
    side: TradeSide
    price: Decimal
    quantity: Decimal
    fee: Decimal | None
    realized_pnl: Decimal | None
    time: datetime
    trade_id: str

@dataclass(frozen=True, slots=True)
class CloseEvent:
    closed_side: PositionSide
    pnl: Decimal
    quantity_closed: Decimal
    closed_at: datetime

class PositionsEngine:
    def __init__(self, repo: PositionsRepository):
        self._repo = repo

    async def apply(self, trade: TradeEvent) -> list[CloseEvent]:
        own_side = PositionSide.LONG if trade.side == TradeSide.BUY else PositionSide.SHORT
        opp_side = PositionSide.SHORT if trade.side == TradeSide.BUY else PositionSide.LONG
        qty_left = trade.quantity
        fee = trade.fee or _D0
        events: list[CloseEvent] = []

        opposite = await self._repo.find_open(
            trade.user_id, trade.api_key_id, trade.exchange, trade.market_type, trade.symbol, opp_side
        )
        if opposite is not None:
            consumed, pnl = self._reduce(opposite, trade, qty_left, fee)
            events.append(CloseEvent(opp_side, pnl, consumed, trade.time))
            qty_left -= consumed
            fee = _D0
        elif self._is_orphan_close(trade):
            return events

        if qty_left <= _D0:
            return events

        if self._can_open(own_side, trade.market_type):
            await self._open_or_extend(trade, own_side, qty_left, fee)
        else:
            logger.info(
                f"[positions] spot oversell skipped {trade.exchange.value}/{trade.symbol} "
                f"qty={qty_left} trade_id={trade.trade_id}"
            )
        return events

    @staticmethod
    def _can_open(side: PositionSide, market_type: MarketType) -> bool:
        return market_type == MarketType.FUTURES or side == PositionSide.LONG

    @staticmethod
    def _is_orphan_close(trade: TradeEvent) -> bool:
        return (
            trade.market_type == MarketType.FUTURES
            and trade.realized_pnl is not None
            and trade.realized_pnl != _D0
        )

    @classmethod
    def _reduce(cls, position: Position, trade: TradeEvent, qty_left: Decimal, fee: Decimal) -> tuple[Decimal, Decimal]:
        if trade.market_type == MarketType.SPOT:
            consumed, pnl = cls._fifo_consume(position, qty_left, trade.price)
        else:
            consumed = min(qty_left, position.qty)
            pnl = trade.realized_pnl if trade.realized_pnl is not None else cls._mark_pnl(position, trade.price, consumed)
            position.qty = position.qty - consumed

        position.realized_pnl = position.realized_pnl + pnl
        position.fees_quote = position.fees_quote + fee
        position.trade_count = position.trade_count + 1

        if position.qty <= _D0:
            position.status = PositionStatus.CLOSED
            position.exit_price = trade.price
            position.closed_at = trade.time

        return consumed, pnl

    @staticmethod
    def _mark_pnl(position: Position, exit_price: Decimal, consumed: Decimal) -> Decimal:
        direction = Decimal(1) if position.side == PositionSide.LONG else Decimal(-1)
        return (exit_price - position.entry_price) * consumed * direction

    @staticmethod
    def _fifo_consume(position: Position, qty_left: Decimal, exit_price: Decimal) -> tuple[Decimal, Decimal]:
        fills = [[Decimal(p), Decimal(q)] for p, q in (position.entry_fills or [])]
        consumed = _D0
        pnl = _D0

        while qty_left > 0 and fills:
            entry_price, entry_qty = fills[0]
            matched = min(qty_left, entry_qty)
            pnl += (exit_price - entry_price) * matched
            fills[0][1] -= matched
            qty_left -= matched
            consumed += matched
            if fills[0][1] <= _D0:
                fills.pop(0)

        position.entry_fills = [[str(p), str(q)] for p, q in fills]
        position.qty = position.qty - consumed
        return consumed, pnl

    async def _open_or_extend(self, trade: TradeEvent, side: PositionSide, qty: Decimal, fee: Decimal) -> None:
        existing = await self._repo.find_open(
            trade.user_id, trade.api_key_id, trade.exchange, trade.market_type, trade.symbol, side
        )
        if existing is None:
            self._repo.add(Position(
                user_id=trade.user_id, api_key_id=trade.api_key_id, exchange=trade.exchange,
                market_type=trade.market_type, symbol=trade.symbol, side=side,
                status=PositionStatus.OPEN, qty=qty, entry_price=trade.price,
                entry_notional=trade.price * qty,
                realized_pnl=_D0, fees_quote=fee, averaged_down=False,
                opened_at=trade.time, trade_count=1,
                entry_fills=self._fills_init(trade.market_type, trade.price, qty)
            ))
            await self._repo.flush()
            return

        if (side == PositionSide.LONG and trade.price < existing.entry_price) or \
                (side == PositionSide.SHORT and trade.price > existing.entry_price):
            existing.averaged_down = True

        new_qty = existing.qty + qty
        existing.entry_price = ((existing.entry_price * existing.qty) + (trade.price * qty)) / new_qty
        existing.qty = new_qty
        existing.entry_notional = existing.entry_notional + (trade.price * qty)
        existing.fees_quote = existing.fees_quote + fee
        existing.trade_count = existing.trade_count + 1

        if trade.market_type == MarketType.SPOT:
            existing.entry_fills = list(existing.entry_fills or []) + [[str(trade.price), str(qty)]]

    @staticmethod
    def _fills_init(market_type: MarketType, price: Decimal, qty: Decimal) -> list:
        return [[str(price), str(qty)]] if market_type == MarketType.SPOT else []
