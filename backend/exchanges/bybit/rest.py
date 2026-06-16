import hmac, time, asyncio, hashlib

from domain.enums import Exchange, FetchMode, MarketType
from shared.exceptions import KeyAccessRestrictedError, KeyNotReadOnlyError
from utils.logger import logger

from ..client import BaseExchangeClient
from ..config import ENDPOINTS
from ..helpers import build_url, dec, dec_opt, from_ms, klines_from_rows, qs, to_side
from ..types import KeyCapabilities, NormalizedTrade, SignedRequest
from .errors import BybitErrors

def parse_execution(row: dict, mt: MarketType) -> NormalizedTrade:
    position_idx = row.get("positionIdx")
    return NormalizedTrade(
        id=row["execId"],
        exchange=Exchange.BYBIT,
        market_type=mt,
        symbol=row["symbol"],
        time=from_ms(row["execTime"]),
        price=dec(row["execPrice"]),
        quantity=dec(row["execQty"]),
        side=to_side(row["side"]),
        fee=dec_opt(row.get("execFee")),
        fee_asset=row.get("feeCurrency"),
        order_id=row.get("orderId"),
        is_maker=row.get("isMaker"),
        quote_qty=dec_opt(row.get("execValue")),
        position_side=("long" if position_idx == 1 else "short" if position_idx == 2 else None)
    )

class BybitClient(BaseExchangeClient):
    exchange = Exchange.BYBIT

    _EXECUTIONS = "/v5/execution/list"
    _CLOSED_PNL = "/v5/position/closed-pnl"
    _QUERY_API = "/v5/user/query-api"
    _WALLET_BALANCE = "/v5/account/wallet-balance"
    _KLINE = "/v5/market/kline"

    _KLINE_INTERVAL = "15"
    _KLINE_LIMIT = 1000
    _KLINE_NEWEST_FIRST = True
    _RECV_WINDOW = "5000"
    _POOL_TRADES = "trades"
    _POOL_USER = "user"
    _POOL_ACCOUNT = "account"
    _POOL_MARKET = "market"
    _CATEGORY = {MarketType.SPOT: "spot", MarketType.FUTURES: "linear"}
    _pnl_map: dict | None = None

    def fetch_mode(self, market_type: MarketType) -> str:
        return FetchMode.CURSOR

    def _build_request(self, method: str, base: str, path: str, params: dict, signed: bool) -> SignedRequest:
        query = qs(params)
        url = build_url(base, path, query)

        if signed:
            ts = str(int(time.time() * 1000))
            payload = ts + self.api_key + self._RECV_WINDOW + query
            sign = hmac.new(self.api_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            headers = {
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-SIGN": sign,
                "X-BAPI-TIMESTAMP": ts,
                "X-BAPI-RECV-WINDOW": self._RECV_WINDOW
            }
        else:
            headers = {}

        return SignedRequest(url=url, headers=headers)

    def _check_payload(self, data):
        if data.get("retCode", 0) != 0:
            raise BybitErrors.parse(data["retCode"], data.get("retMsg", ""))

    def _unwrap(self, data):
        return data.get("result", {})

    async def validate_credentials(self) -> KeyCapabilities:
        url = ENDPOINTS[Exchange.BYBIT].url
        account_uid, ip_restricted, permissions = await self._assert_read_only()

        spot_allowed = bool(permissions.get("Spot"))
        futures_allowed = bool(permissions.get("ContractTrade")) or bool(permissions.get("Derivatives"))
        if not spot_allowed and not futures_allowed:
            raise KeyAccessRestrictedError(
                "Bybit: this key has neither SPOT nor Contract read permission — "
                "tick at least one of them when creating the key on Bybit"
            )

        spot_err, fut_err = await asyncio.gather(
            self._probe(url, self._EXECUTIONS, self._POOL_TRADES, {"category": "spot", "limit": "1"}),
            self._probe(url, self._EXECUTIONS, self._POOL_TRADES, {"category": "linear", "limit": "1"})
        )

        return self._resolve_caps(
            spot_allowed=spot_allowed, spot_err=spot_err,
            futures_allowed=futures_allowed, fut_err=fut_err,
            account_uid=account_uid, ip_restricted=ip_restricted
        )

    async def _assert_read_only(self) -> tuple[str | None, bool, dict]:
        data = await self._request("GET", ENDPOINTS[Exchange.BYBIT].url, self._QUERY_API, self._POOL_USER)
        if data.get("readOnly") != 1:
            raise KeyNotReadOnlyError(
                "Bybit: this key is Read-Write — recreate the key on Bybit with API Key Permissions = Read-Only"
            )

        uid = data.get("userID")
        ips = data.get("ips") or []
        ip_restricted = bool(ips) and ips != ["*"]
        return str(uid) if uid is not None else None, ip_restricted, data.get("permissions") or {}

    async def fetch_trades_paginated(self, market_type: MarketType, cursor: str | None = None):
        params = {"category": self._CATEGORY[market_type], "limit": "100"}
        if cursor:
            params["cursor"] = cursor

        result = await self._request("GET", ENDPOINTS[Exchange.BYBIT].url, self._EXECUTIONS, self._POOL_TRADES, params)
        rows = [r for r in result.get("list", []) if r.get("execType") == "Trade"]
        return [parse_execution(r, market_type) for r in rows], result.get("nextPageCursor")

    async def enrich_trades(self, market_type: MarketType, trades: list):
        if market_type != MarketType.FUTURES:
            return

        if self._pnl_map is None:
            self._pnl_map = await self._closed_pnl_map()
        if not self._pnl_map:
            return

        seen = set()
        for t in trades:
            pnl = self._pnl_map.get(t.order_id)
            if pnl is not None and t.order_id not in seen:
                t.realized_pnl = pnl
                seen.add(t.order_id)

    async def _closed_pnl_map(self) -> dict:
        out = {}
        cursor = None
        while True:
            params = {"category": "linear", "limit": "100"}
            if cursor:
                params["cursor"] = cursor

            result = await self._request("GET", ENDPOINTS[Exchange.BYBIT].url, self._CLOSED_PNL, self._POOL_TRADES, params)
            for row in result.get("list", []):
                order_id = row.get("orderId")
                pnl = dec_opt(row.get("closedPnl"))
                if order_id and pnl is not None:
                    out[order_id] = pnl

            cursor = result.get("nextPageCursor")
            if not cursor:
                return out

    async def fetch_spot_balances(self) -> dict:
        result = await self._request("GET", ENDPOINTS[Exchange.BYBIT].url, self._WALLET_BALANCE, self._POOL_ACCOUNT, {"accountType": "UNIFIED"})
        out: dict = {}
        for acct in result.get("list", []):
            for coin in acct.get("coin", []):
                total = dec(coin.get("walletBalance") or 0)
                if total > 0:
                    out[coin["coin"]] = total
        return out

    async def fetch_klines(self, market_type: MarketType, symbol: str, start_ms: int, end_ms: int):
        params = {
            "category": self._CATEGORY[market_type],
            "symbol": symbol,
            "interval": self._KLINE_INTERVAL,
            "start": start_ms,
            "end": end_ms,
            "limit": self._KLINE_LIMIT
        }
        result = await self._request("GET", ENDPOINTS[Exchange.BYBIT].url, self._KLINE, self._POOL_MARKET, params, signed=False)
        return klines_from_rows(result.get("list", []), newest_first=True)
