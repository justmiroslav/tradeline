from domain.enums import Exchange, MarketType

from ..config import ENDPOINTS
from ..helpers import dec, dec_opt, from_ms
from ..ws.ok_style import OKStyleWSHandler
from .errors import BitgetErrors
from .rest import _build_normalized

class BitgetWSHandler(OKStyleWSHandler):
    exchange = Exchange.BITGET

    _AUTH_PATH = "/user/verify"
    _PING_INTERVAL = 30
    _INST_MAP = {MarketType.SPOT: "SPOT", MarketType.FUTURES: "USDT-FUTURES"}
    _SUBSCRIBE_EXTRA = {"instId": "default"}
    _ERRORS = BitgetErrors

    def _ws_url(self) -> str:
        return ENDPOINTS[Exchange.BITGET].ws

    def _parse_ws_fill(self, row: dict, mt: MarketType):
        price = dec(row["fillPrice"])
        quantity = dec(row["baseVolume"])
        fee_raw = dec_opt(row.get("fillFee"))
        scope = row.get("tradeScope")
        pos_side = row.get("posSide")
        return _build_normalized(row, mt,
            price=price,
            quantity=quantity,
            fee_raw=fee_raw,
            fee_asset=row.get("fillFeeCoin"),
            realized_pnl=dec_opt(row.get("pnl")) if mt == MarketType.FUTURES else None,
            position_side=pos_side if pos_side in ("long", "short") else None,
            is_maker=True if scope == "M" else False if scope == "T" else None,
            symbol=row.get("instId") or row["symbol"],
            time_=from_ms(row.get("fillTime") or row["uTime"]),
            quote_qty=price * quantity)
