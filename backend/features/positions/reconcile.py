from decimal import Decimal

from domain.enums import PositionStatus
from domain.models import Position

_QUOTES = ("USDT", "USDC", "BUSD", "FDUSD", "USD")
_REL_TOL = Decimal("0.02")
_MIN_KEEP = Decimal("0.01")

def _base_asset(symbol: str) -> str | None:
    for quote in _QUOTES:
        if symbol.endswith(quote) and len(symbol) > len(quote):
            return symbol[: -len(quote)]
    return None

def reconcile_open_spot(positions, balances: dict) -> list[Position]:
    created: list[Position] = []
    for pos in positions:
        base = _base_asset(pos.symbol)
        if base is None:
            continue
        held = Decimal(balances.get(base, 0))
        qty = pos.qty
        if qty <= 0 or held >= qty * (Decimal(1) - _REL_TOL):
            continue
        if held <= qty * _MIN_KEEP:
            pos.status = PositionStatus.INCOMPLETE
            continue
        created.append(_split_broken(pos, qty - held))
    return created

def _split_broken(pos: Position, missing: Decimal) -> Position:
    fills = [[Decimal(price), Decimal(qty)] for price, qty in (pos.entry_fills or [])]
    broken: list[list[Decimal]] = []
    take = missing
    while take > 0 and fills:
        price, qty = fills[0]
        used = min(take, qty)
        broken.append([price, used])
        fills[0][1] -= used
        take -= used
        if fills[0][1] <= 0:
            fills.pop(0)

    broken_qty = sum((qty for _, qty in broken), Decimal(0))
    broken_notional = sum((price * qty for price, qty in broken), Decimal(0))
    kept_qty = pos.qty - broken_qty
    kept_notional = pos.entry_notional - broken_notional

    incomplete = Position(
        user_id=pos.user_id, api_key_id=pos.api_key_id, exchange=pos.exchange,
        market_type=pos.market_type, symbol=pos.symbol, side=pos.side,
        status=PositionStatus.INCOMPLETE, qty=broken_qty,
        entry_price=broken_notional / broken_qty if broken_qty > 0 else pos.entry_price,
        entry_notional=broken_notional, realized_pnl=Decimal(0), fees_quote=Decimal(0),
        entry_fills=[[str(price), str(qty)] for price, qty in broken], opened_at=pos.opened_at,
        trade_count=1, averaged_down=False
    )

    pos.qty = kept_qty
    pos.entry_notional = kept_notional
    pos.entry_price = kept_notional / kept_qty if kept_qty > 0 else pos.entry_price
    pos.entry_fills = [[str(price), str(qty)] for price, qty in fills]
    return incomplete
