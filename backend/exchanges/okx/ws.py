from domain.enums import Exchange, MarketType

from ..config import ENDPOINTS
from ..helpers import dec_opt, from_ms
from ..ws.ok_style import OKStyleWSHandler
from .errors import OKXErrors
from .rest import _build_normalized

class OKXWSHandler(OKStyleWSHandler):
    exchange = Exchange.OKX

    _AUTH_PATH = "/users/self/verify"
    _PING_INTERVAL = 25
    _INST_MAP = {MarketType.SPOT: "SPOT", MarketType.FUTURES: "SWAP"}
    _ERRORS = OKXErrors

    def _ws_url(self) -> str:
        return ENDPOINTS[Exchange.OKX].ws

    def _parse_ws_fill(self, row: dict, mt: MarketType):
        return _build_normalized(row, mt,
            id_=row.get("tradeId") or row["ordId"],
            time_=from_ms(row.get("fillTime") or row["uTime"]),
            fee_raw=dec_opt(row.get("fillFee")),
            fee_asset=row.get("fillFeeCcy"))
