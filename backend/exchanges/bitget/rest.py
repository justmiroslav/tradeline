import time, asyncio

from domain.enums import Exchange, FetchMode, MarketType
from shared.exceptions import InvalidCredentialsError, KeyAccessRestrictedError, KeyNotReadOnlyError
from utils.logger import logger

from ..client import BaseExchangeClient
from ..config import ENDPOINTS
from ..helpers import abs_or_none, build_url, dec, dec_opt, from_ms, klines_from_rows, qs, sign_b64, to_side
from ..types import KeyCapabilities, NormalizedTrade, SignedRequest
from .errors import BitgetErrors

def _futures_position_side(trade_side: str | None, pos_mode: str | None) -> str | None:
    if pos_mode != "hedge_mode" or not trade_side:
        return None
    s = trade_side.lower()
    if "long" in s:
        return "long"
    if "short" in s:
        return "short"
    return None

def _build_normalized(row: dict, mt: MarketType, *, price, quantity, fee_raw, fee_asset, realized_pnl, position_side, is_maker, symbol, time_, quote_qty) -> NormalizedTrade:
    return NormalizedTrade(
        id=row["tradeId"],
        exchange=Exchange.BITGET,
        market_type=mt,
        symbol=symbol,
        time=time_,
        price=price,
        quantity=quantity,
        side=to_side(row["side"]),
        fee=abs_or_none(fee_raw),
        fee_asset=fee_asset,
        order_id=row.get("orderId"),
        realized_pnl=realized_pnl,
        is_maker=is_maker,
        quote_qty=quote_qty,
        position_side=position_side
    )

def parse_rest_fill(row: dict, market_type: MarketType) -> NormalizedTrade:
    if market_type == MarketType.SPOT:
        fd = row.get("feeDetail") or {}
        price = dec(row["priceAvg"])
        quantity = dec(row["size"])
        notional = dec_opt(row.get("amount"))
        realized_pnl = None
        position_side = None
    else:
        fd_list = row.get("feeDetail") or []
        fd = fd_list[0] if fd_list else {}
        price = dec(row["price"])
        quantity = dec(row["baseVolume"])
        notional = dec_opt(row.get("quoteVolume"))
        realized_pnl = dec_opt(row.get("profit"))
        position_side = _futures_position_side(row.get("tradeSide"), row.get("posMode"))

    fee_raw = dec_opt(fd.get("totalFee"))
    scope = row.get("tradeScope")
    return _build_normalized(row, market_type,
        price=price,
        quantity=quantity,
        fee_raw=fee_raw,
        fee_asset=fd.get("feeCoin"),
        realized_pnl=realized_pnl,
        position_side=position_side,
        is_maker=True if scope == "maker" else False if scope == "taker" else None,
        symbol=row["symbol"],
        time_=from_ms(row["cTime"]),
        quote_qty=notional if notional is not None else price * quantity)

class BitgetClient(BaseExchangeClient):
    exchange = Exchange.BITGET

    _SPOT_FILLS = "/api/v2/spot/trade/fills"
    _SPOT_INFO = "/api/v2/spot/account/info"
    _SPOT_ASSETS = "/api/v2/spot/account/assets"
    _SPOT_HISTORY_CANDLES = "/api/v2/spot/market/history-candles"

    _FUTURES_FILLS = "/api/v2/mix/order/fills"
    _FUTURES_HISTORY_CANDLES = "/api/v2/mix/market/history-candles"

    _SPOT_GRANULARITY = "15min"
    _FUTURES_GRANULARITY = "15m"
    _KLINE_LIMIT = "200"
    _KLINE_NEWEST_FIRST = True
    _POOL_TRADES = "trades"
    _POOL_ACCOUNT = "account"
    _POOL_MARKET = "market"

    _WRITE_AUTHORITIES = frozenset({
        "coow", "cpow", "stow", "smow", "ttow", "wtow",
        "wwow", "chow", "p2p", "pllw", "taxw"
    })
    _SPOT_AUTHORITIES = frozenset({"stor", "stow"})
    _FUTURES_AUTHORITIES = frozenset({"coor", "coow", "cpor", "cpow"})

    def fetch_mode(self, market_type: MarketType) -> str:
        return FetchMode.CURSOR

    def _build_request(self, method: str, base: str, path: str, params: dict, signed: bool) -> SignedRequest:
        query = qs(params)
        full_path = f"{path}?{query}" if query else path
        url = build_url(base, path, query)

        if signed:
            ts = str(int(time.time() * 1000))
            msg = ts + method.upper() + full_path
            sign = sign_b64(self.api_secret, msg)
            headers = {
                "ACCESS-KEY": self.api_key,
                "ACCESS-SIGN": sign,
                "ACCESS-PASSPHRASE": self.passphrase or "",
                "ACCESS-TIMESTAMP": ts,
                "Content-Type": "application/json",
                "locale": "en-US"
            }
        else:
            headers = {}

        return SignedRequest(url=url, headers=headers)

    def _check_payload(self, data):
        if data.get("code") != "00000":
            raise BitgetErrors.parse(data.get("code", ""), data.get("msg", ""))

    async def validate_credentials(self) -> KeyCapabilities:
        if not self.passphrase:
            raise InvalidCredentialsError(
                "Bitget: passphrase is required — enter the passphrase you set when creating the API key (separate from the API secret)"
            )

        account_uid, ip_restricted, authorities = await self._assert_read_only()
        spot_allowed = bool(authorities & self._SPOT_AUTHORITIES)
        futures_allowed = bool(authorities & self._FUTURES_AUTHORITIES)
        if not spot_allowed and not futures_allowed:
            raise KeyAccessRestrictedError(
                "Bitget: this key has neither Spot Trade nor Futures Orders permission — "
                "tick at least one of them when creating the key on Bitget"
            )

        url = ENDPOINTS[Exchange.BITGET].url
        spot_err, fut_err = await asyncio.gather(
            self._probe(url, self._SPOT_FILLS, self._POOL_TRADES, {"limit": "1"}),
            self._probe(url, self._FUTURES_FILLS, self._POOL_TRADES, {"productType": "USDT-FUTURES", "limit": "1"})
        )

        return self._resolve_caps(
            spot_allowed=spot_allowed, spot_err=spot_err,
            futures_allowed=futures_allowed, fut_err=fut_err,
            account_uid=account_uid, ip_restricted=ip_restricted
        )

    async def _assert_read_only(self) -> tuple[str | None, bool, frozenset[str]]:
        data = await self._request("GET", ENDPOINTS[Exchange.BITGET].url, self._SPOT_INFO, self._POOL_ACCOUNT)
        info = data.get("data") or {}
        raw = info.get("authorities") or []
        if not raw:
            raise KeyNotReadOnlyError("Bitget: cannot read key permissions from /spot/account/info")

        tokens = frozenset(str(a).strip().lower() for a in raw if str(a).strip())
        write_present = tokens & self._WRITE_AUTHORITIES
        if write_present:
            raise KeyNotReadOnlyError(
                f"Bitget: this key grants write scopes ({', '.join(sorted(write_present))}) — "
                "recreate it on Bitget with only Read-Only permissions ticked"
            )

        uid = info.get("userId")
        ips = info.get("ips")
        ip_restricted = bool(ips) if isinstance(ips, list) else bool(str(ips or "").strip())
        return str(uid) if uid is not None else None, ip_restricted, tokens

    async def fetch_trades_paginated(self, market_type: MarketType, cursor: str | None = None):
        url = ENDPOINTS[Exchange.BITGET].url

        if market_type == MarketType.SPOT:
            path = self._SPOT_FILLS
            params = {"limit": "100"}
        else:
            path = self._FUTURES_FILLS
            params = {"productType": "USDT-FUTURES", "limit": "100"}

        if cursor:
            params["idLessThan"] = cursor

        data = await self._request("GET", url, path, self._POOL_TRADES, params)

        if market_type == MarketType.SPOT:
            rows = data.get("data") or []
            next_cursor = rows[-1].get("tradeId") if rows else None
        else:
            data_obj = data.get("data") or {}
            rows = data_obj.get("fillList") or []
            next_cursor = data_obj.get("endId") or (rows[-1].get("tradeId") if rows else None)

        return [parse_rest_fill(r, market_type) for r in rows], next_cursor

    async def fetch_spot_balances(self) -> dict:
        data = await self._request("GET", ENDPOINTS[Exchange.BITGET].url, self._SPOT_ASSETS, self._POOL_ACCOUNT)
        out: dict = {}
        for coin in data.get("data") or []:
            total = dec(coin.get("available") or 0) + dec(coin.get("frozen") or 0) + dec(coin.get("locked") or 0)
            if total > 0:
                out[coin["coin"]] = total
        return out

    async def fetch_klines(self, market_type: MarketType, symbol: str, start_ms: int, end_ms: int):
        params = {"symbol": symbol, "endTime": str(end_ms), "limit": self._KLINE_LIMIT}
        if market_type == MarketType.SPOT:
            path = self._SPOT_HISTORY_CANDLES
            params["granularity"] = self._SPOT_GRANULARITY
        else:
            path = self._FUTURES_HISTORY_CANDLES
            params["granularity"] = self._FUTURES_GRANULARITY
            params["productType"] = "USDT-FUTURES"

        data = await self._request("GET", ENDPOINTS[Exchange.BITGET].url, path, self._POOL_MARKET, params, signed=False)
        return [k for k in klines_from_rows(data.get("data", [])) if k.time_ms >= start_ms]
