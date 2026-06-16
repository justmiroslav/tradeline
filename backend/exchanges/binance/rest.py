import hmac, json, time, asyncio, hashlib

from domain.enums import Exchange, FetchMode, MarketType, TradeSide
from shared.exceptions import KeyNotReadOnlyError
from utils.logger import logger

from ..client import BaseExchangeClient
from ..config import ENDPOINTS
from ..helpers import FETCH_ERRORS, build_url, dec, dec_opt, from_ms, klines_from_rows, qs
from ..types import KeyCapabilities, NormalizedTrade, SignedRequest
from .errors import BinanceErrors

class BinanceClient(BaseExchangeClient):
    exchange = Exchange.BINANCE

    _SPOT_ACCOUNT = "/api/v3/account"
    _SPOT_TRADES = "/api/v3/myTrades"
    _SPOT_KLINES = "/api/v3/klines"
    _SPOT_TICKER_24H = "/api/v3/ticker/24hr"
    _API_RESTRICTIONS = "/sapi/v1/account/apiRestrictions"

    _FUTURES_ACCOUNT = "/fapi/v2/account"
    _FUTURES_TRADES = "/fapi/v1/userTrades"
    _FUTURES_KLINES = "/fapi/v1/klines"
    _FUTURES_POSITIONS = "/fapi/v2/positionRisk"

    _KLINE_INTERVAL = "15m"
    _SPOT_KLINE_LIMIT = 1000
    _FUTURES_KLINE_LIMIT = 1500
    _POOL_SPOT = "spot"
    _POOL_FUT = "fut"

    _REJECT_PERMS = (
        "enableSpotAndMarginTrading", "enableMargin",
        "enableWithdrawals", "enableInternalTransfer",
        "enablePortfolioMarginTrading", "enableVanillaOptions",
        "permitsUniversalTransfer"
    )

    def fetch_mode(self, market_type: MarketType) -> str:
        return FetchMode.SYMBOL_SCAN

    def _build_request(self, method: str, base: str, path: str, params: dict, signed: bool) -> SignedRequest:
        if signed:
            params = {**params, "timestamp": int(time.time() * 1000)}
            query = qs(params)
            sig = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
            url = f"{base}{path}?{query}&signature={sig}"
            headers = {"X-MBX-APIKEY": self.api_key}
        else:
            url = build_url(base, path, qs(params))
            headers = {}

        return SignedRequest(url=url, headers=headers)

    def _check_payload(self, data):
        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceErrors.parse(data["code"], data.get("msg", ""))

    async def validate_credentials(self) -> KeyCapabilities:
        ip_restricted, futures_enabled = await self._assert_read_only()

        spot_res, fut_err = await asyncio.gather(
            self._probe_data(ENDPOINTS[Exchange.BINANCE].url, self._SPOT_ACCOUNT, self._POOL_SPOT, weight=20),
            self._probe(ENDPOINTS[Exchange.BINANCE].futures_url, self._FUTURES_ACCOUNT, self._POOL_FUT, weight=5)
        )
        spot_data, spot_err = spot_res
        uid = spot_data.get("uid") if spot_data else None
        return self._resolve_caps(
            spot_allowed=True, spot_err=spot_err,
            futures_allowed=futures_enabled, fut_err=fut_err,
            account_uid=str(uid) if uid is not None else None,
            ip_restricted=ip_restricted
        )

    async def _assert_read_only(self) -> tuple[bool, bool]:
        data = await self._request("GET", ENDPOINTS[Exchange.BINANCE].url, self._API_RESTRICTIONS, self._POOL_SPOT, weight=1)
        enabled = [k for k in self._REJECT_PERMS if data.get(k)]
        if enabled:
            raise KeyNotReadOnlyError(
                f"Binance: key grants {', '.join(enabled)}. "
                "Edit the key on Binance and untick every box except 'Enable Reading'."
            )
        return bool(data.get("ipRestrict")), bool(data.get("enableFutures"))

    async def fetch_trades_by_symbol(self, market_type: MarketType, symbol: str, since_id: str | None = None, start_ms: int | None = None):
        if market_type == MarketType.SPOT:
            base = ENDPOINTS[Exchange.BINANCE].url
            path = self._SPOT_TRADES
            pool = self._POOL_SPOT
            weight = 20
        else:
            base = ENDPOINTS[Exchange.BINANCE].futures_url
            path = self._FUTURES_TRADES
            pool = self._POOL_FUT
            weight = 5

        params = {"symbol": symbol, "limit": 1000}
        if since_id:
            params["fromId"] = int(since_id) + 1
        elif start_ms:
            params["startTime"] = start_ms

        try:
            data = await self._request("GET", base, path, pool, params, weight=weight)
        except FETCH_ERRORS as e:
            logger.warning(f"[Binance] {market_type.value}/{symbol}: {e}")
            return []

        if not isinstance(data, list):
            return []
        return [self._parse(row, market_type) for row in data]

    async def fetch_klines(self, market_type: MarketType, symbol: str, start_ms: int, end_ms: int):
        if market_type == MarketType.SPOT:
            base = ENDPOINTS[Exchange.BINANCE].url
            path = self._SPOT_KLINES
            pool = self._POOL_SPOT
            limit = self._SPOT_KLINE_LIMIT
            weight = 2
        else:
            base = ENDPOINTS[Exchange.BINANCE].futures_url
            path = self._FUTURES_KLINES
            pool = self._POOL_FUT
            limit = self._FUTURES_KLINE_LIMIT
            weight = 10

        params = {
            "symbol": symbol,
            "interval": self._KLINE_INTERVAL,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": limit
        }
        data = await self._request("GET", base, path, pool, params, signed=False, weight=weight)
        if not isinstance(data, list):
            return []
        return klines_from_rows(data)

    async def fetch_ticker_24h(self, symbols: list[str] | None = None) -> list:
        if symbols:
            params = {"symbols": json.dumps(symbols, separators=(",", ":"))}
            weight = 40
        else:
            params = None
            weight = 80
        data = await self._request("GET", ENDPOINTS[Exchange.BINANCE].url, self._SPOT_TICKER_24H, self._POOL_SPOT, params, signed=False, weight=weight)
        return data if isinstance(data, list) else []

    async def fetch_scan_symbols(self, market_type: MarketType, universe: list):
        known = set(universe)
        if market_type == MarketType.SPOT:
            data = await self._request("GET", ENDPOINTS[Exchange.BINANCE].url, self._SPOT_ACCOUNT, self._POOL_SPOT, weight=20)
            held = {b["asset"] for b in data.get("balances", []) if float(b.get("free") or 0) + float(b.get("locked") or 0) > 0}
            return sorted({f"{a}USDT" for a in held} & known)

        data = await self._request("GET", ENDPOINTS[Exchange.BINANCE].futures_url, self._FUTURES_POSITIONS, self._POOL_FUT, weight=5)
        rows = data if isinstance(data, list) else []
        return sorted({p["symbol"] for p in rows if float(p.get("positionAmt") or 0) != 0} & known)

    async def fetch_spot_balances(self) -> dict:
        data = await self._request("GET", ENDPOINTS[Exchange.BINANCE].url, self._SPOT_ACCOUNT, self._POOL_SPOT, weight=20)
        out: dict = {}
        for b in data.get("balances", []):
            total = dec(b.get("free") or 0) + dec(b.get("locked") or 0)
            if total > 0:
                out[b["asset"]] = total
        return out

    @staticmethod
    def _parse(row: dict, market_type: MarketType) -> NormalizedTrade:
        is_buyer = row["isBuyer"] if market_type == MarketType.SPOT else row["side"] == "BUY"
        is_maker_key = "isMaker" if market_type == MarketType.SPOT else "maker"
        return NormalizedTrade(
            id=str(row["id"]),
            exchange=Exchange.BINANCE,
            market_type=market_type,
            symbol=row["symbol"],
            time=from_ms(row["time"]),
            price=dec(row["price"]),
            quantity=dec(row["qty"]),
            side=TradeSide.BUY if is_buyer else TradeSide.SELL,
            fee=dec_opt(row.get("commission")),
            fee_asset=row.get("commissionAsset"),
            order_id=str(row["orderId"]),
            realized_pnl=dec_opt(row.get("realizedPnl")),
            is_maker=row.get(is_maker_key),
            quote_qty=dec_opt(row.get("quoteQty")),
            position_side=row.get("positionSide")
        )
