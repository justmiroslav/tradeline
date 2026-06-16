import asyncio

from datetime import datetime, timezone

from domain.enums import Exchange, FetchMode, MarketType
from shared.exceptions import InvalidCredentialsError, KeyNotReadOnlyError

from ..client import BaseExchangeClient
from ..config import ENDPOINTS
from ..helpers import abs_or_none, build_url, dec, dec_opt, from_ms, klines_from_rows, qs, sign_b64, to_side
from ..types import KeyCapabilities, NormalizedTrade, SignedRequest
from .errors import OKXErrors

def to_symbol(inst_id: str) -> str:
    return inst_id.replace("-SWAP", "").replace("-", "")

def to_inst_id(symbol: str, market_type: MarketType) -> str:
    inst = f"{symbol.removesuffix('USDT')}-USDT"
    return f"{inst}-SWAP" if market_type == MarketType.FUTURES else inst

def _build_normalized(row: dict, mt: MarketType, *, id_, time_, fee_raw, fee_asset) -> NormalizedTrade:
    price = dec(row["fillPx"])
    quantity = dec(row["fillSz"])
    exec_type = row.get("execType")
    pos_side = row.get("posSide")
    return NormalizedTrade(
        id=id_,
        exchange=Exchange.OKX,
        market_type=mt,
        symbol=to_symbol(row["instId"]),
        time=time_,
        price=price,
        quantity=quantity,
        side=to_side(row["side"]),
        fee=abs_or_none(fee_raw),
        fee_asset=fee_asset,
        order_id=row.get("ordId"),
        realized_pnl=dec_opt(row.get("fillPnl")) if mt == MarketType.FUTURES else None,
        is_maker=True if exec_type == "M" else False if exec_type == "T" else None,
        quote_qty=dec_opt(row.get("fillNotionalUsd")) or price * quantity,
        position_side=pos_side if pos_side in ("long", "short") else None
    )

def parse_rest_fill(row: dict, mt: MarketType) -> NormalizedTrade:
    return _build_normalized(row, mt,
        id_=row.get("tradeId") or row["billId"],
        time_=from_ms(row.get("fillTime") or row["ts"]),
        fee_raw=dec_opt(row.get("fee")),
        fee_asset=row.get("feeCcy"))

class OKXClient(BaseExchangeClient):
    exchange = Exchange.OKX

    _ACCOUNT_CONFIG = "/api/v5/account/config"
    _ACCOUNT_BALANCE = "/api/v5/account/balance"
    _FILLS_HISTORY = "/api/v5/trade/fills-history"
    _CANDLES = "/api/v5/market/candles"
    _HISTORY_CANDLES = "/api/v5/market/history-candles"

    _KLINE_BAR = "15m"
    _KLINE_LIMIT = 100
    _KLINE_NEWEST_FIRST = True
    _LIVE_CANDLES_DEPTH_BARS = 1440
    _LIVE_CANDLES_SAFETY_BARS = 96
    _POOL_TRADES = "trades"
    _POOL_ACCOUNT = "account"
    _POOL_MARKET = "market"
    _INST_TYPE = {MarketType.SPOT: "SPOT", MarketType.FUTURES: "SWAP"}

    def fetch_mode(self, market_type: MarketType) -> str:
        return FetchMode.CURSOR

    def _build_request(self, method: str, base: str, path: str, params: dict, signed: bool) -> SignedRequest:
        query = qs(params)
        full_path = f"{path}?{query}" if query else path
        url = build_url(base, path, query)

        if signed:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            msg = ts + method.upper() + full_path
            sign = sign_b64(self.api_secret, msg)
            headers = {
                "OK-ACCESS-KEY": self.api_key,
                "OK-ACCESS-SIGN": sign,
                "OK-ACCESS-TIMESTAMP": ts,
                "OK-ACCESS-PASSPHRASE": self.passphrase or "",
                "Content-Type": "application/json"
            }
        else:
            headers = {}

        return SignedRequest(url=url, headers=headers)

    def _check_payload(self, data):
        if data.get("code") != "0":
            raise OKXErrors.parse(data.get("code", ""), data.get("msg", ""))

    async def validate_credentials(self) -> KeyCapabilities:
        if not self.passphrase:
            raise InvalidCredentialsError(
                "OKX: passphrase is required — enter the passphrase you set when creating the API key (separate from the API secret)"
            )

        account_uid, ip_restricted = await self._assert_read_only()

        url = ENDPOINTS[Exchange.OKX].url
        spot_err, fut_err = await asyncio.gather(
            self._probe(url, self._FILLS_HISTORY, self._POOL_TRADES, {"instType": "SPOT", "limit": "1"}),
            self._probe(url, self._FILLS_HISTORY, self._POOL_TRADES, {"instType": "SWAP", "limit": "1"})
        )

        if spot_err is not None and fut_err is not None:
            raise self._both_failed(spot_err, fut_err)

        self._log_validation(spot_err, fut_err, ip_restricted)
        return KeyCapabilities(spot=spot_err is None, futures=fut_err is None, account_uid=account_uid, ip_restricted=ip_restricted)

    async def _assert_read_only(self) -> tuple[str | None, bool]:
        data = await self._request("GET", ENDPOINTS[Exchange.OKX].url, self._ACCOUNT_CONFIG, self._POOL_ACCOUNT)
        rows = data.get("data") or []
        if not rows:
            raise KeyNotReadOnlyError("OKX: cannot read key permissions from /account/config")

        perm = (rows[0].get("perm") or "").strip()
        tokens = {p.strip().lower() for p in perm.split(",") if p.strip()}
        if not tokens:
            raise KeyNotReadOnlyError("OKX: cannot determine key permissions from /account/config")

        if tokens & {"trade", "withdraw"}:
            raise KeyNotReadOnlyError(
                "OKX: this key has trade or withdraw permission — recreate it on OKX with only the 'Read' permission selector"
            )

        uid = rows[0].get("uid")
        ip_restricted = bool((rows[0].get("ip") or "").strip())
        return str(uid) if uid is not None else None, ip_restricted

    async def fetch_trades_paginated(self, market_type: MarketType, cursor: str | None = None):
        params = {"instType": self._INST_TYPE[market_type], "limit": "100"}
        if cursor:
            params["after"] = cursor

        data = await self._request("GET", ENDPOINTS[Exchange.OKX].url, self._FILLS_HISTORY, self._POOL_TRADES, params)
        rows = data.get("data", [])
        next_cursor = rows[-1]["billId"] if rows else None
        return [parse_rest_fill(r, market_type) for r in rows], next_cursor

    async def fetch_spot_balances(self) -> dict:
        data = await self._request("GET", ENDPOINTS[Exchange.OKX].url, self._ACCOUNT_BALANCE, self._POOL_ACCOUNT)
        out: dict = {}
        for acct in data.get("data", []):
            for detail in acct.get("details", []):
                total = dec(detail.get("availBal") or 0) + dec(detail.get("frozenBal") or 0)
                if total > 0:
                    out[detail["ccy"]] = total
        return out

    async def fetch_klines(self, market_type: MarketType, symbol: str, start_ms: int, end_ms: int):
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        live_floor_ms = now_ms - (self._LIVE_CANDLES_DEPTH_BARS - self._LIVE_CANDLES_SAFETY_BARS) * self._KLINE_BAR_MS
        path = self._CANDLES if start_ms >= live_floor_ms else self._HISTORY_CANDLES

        params = {
            "instId": to_inst_id(symbol, market_type),
            "bar": self._KLINE_BAR,
            "before": str(start_ms),
            "after": str(end_ms),
            "limit": str(self._KLINE_LIMIT)
        }
        data = await self._request("GET", ENDPOINTS[Exchange.OKX].url, path, self._POOL_MARKET, params, signed=False)
        return klines_from_rows(data.get("data", []), newest_first=True)
