import uuid

from exchanges.types import NormalizedTrade

def normalized_trade_to_row(user_id: uuid.UUID, api_key_id: uuid.UUID, nt: NormalizedTrade) -> dict:
    return {
        "user_id": user_id,
        "api_key_id": api_key_id,
        "exchange": nt.exchange,
        "market_type": nt.market_type,
        "symbol": nt.symbol,
        "side": nt.side,
        "price": nt.price,
        "quantity": nt.quantity,
        "quote_qty": nt.quote_qty,
        "fee": nt.fee,
        "fee_asset": nt.fee_asset,
        "realized_pnl": nt.realized_pnl,
        "is_maker": nt.is_maker,
        "position_side": nt.position_side,
        "time": nt.time,
        "order_id": nt.order_id,
        "trade_id": str(nt.id)
    }
