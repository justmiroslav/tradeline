import hmac, time, aiohttp, asyncio, hashlib

from uuid import uuid4, UUID

from domain.enums import Exchange, MarketType, TradeSide
from shared.exceptions import ExchangeUnavailableError, RateLimitError
from utils.logger import logger

from ..config import ENDPOINTS, WS_HEARTBEAT, WS_STABLE_SECONDS
from ..errors import WS_AUTH_FATAL, WSAuthFatalError
from ..helpers import dec, dec_opt, from_ms
from ..http_executor import RequestExecutor
from ..types import DecryptedCredentials, NormalizedTrade, SignedRequest
from ..ws import BaseWSHandler
from .errors import BinanceErrors

class BinanceWSHandler(BaseWSHandler):
    exchange = Exchange.BINANCE

    _RECV_WINDOW = 10000
    _LISTEN_KEY_REFRESH_SECONDS = 1800
    _SUBSCRIBE_METHOD = "userDataStream.subscribe.signature"
    _SPOT_EVENT = "executionReport"
    _FUTURES_EVENT = "ORDER_TRADE_UPDATE"
    _TRADE_EXEC_TYPE = "TRADE"
    _FUTURES_LISTEN_KEY_PATH = "/fapi/v1/listenKey"
    _POOL_FUT = "fut"

    def __init__(self, creds: DecryptedCredentials, http: aiohttp.ClientSession, executor: RequestExecutor, api_key_id: UUID, user_id: UUID, capabilities: list[str], on_trade, on_status, on_auth_fatal):
        super().__init__(creds, http, executor, api_key_id, user_id, capabilities, on_trade, on_status, on_auth_fatal)
        self._tasks = []
        self._market_stopped = {}
        self._connected_markets = set()
        self._connected_at = {}

    async def run(self):
        markets = []
        if "spot" in self._capabilities:
            markets.append("spot")
        if "futures" in self._capabilities:
            markets.append("futures")
        if not markets:
            return

        sessions = {"spot": self._spot_session, "futures": self._futures_session}
        for m in markets:
            self._market_stopped[m] = False
            self._tasks.append(asyncio.create_task(self._supervise(m, sessions[m])))

        try:
            await asyncio.gather(*self._tasks)
        finally:
            await self._on_status(self._api_key_id, False)

    async def stop(self):
        self._stopped = True
        for m in self._market_stopped:
            self._market_stopped[m] = True
        for t in self._tasks:
            t.cancel()

    async def _supervise(self, market: str, session_runner):
        attempts = 0

        while not self._stopped and not self._market_stopped[market]:
            self._connected_at.pop(market, None)
            try:
                await session_runner()
            except WSAuthFatalError as e:
                logger.error(f"[WS:binance:{market}] fatal auth error for key={self._api_key_id}: {e} — stopping {market}")
                self._market_stopped[market] = True
                await self._mark_disconnected(market)
                await self._notify_auth_fatal(str(e))
            except asyncio.CancelledError:
                await self._mark_disconnected(market)
                break
            except Exception as e:
                logger.warning(f"[WS:binance:{market}] error: {e}")
                await self._mark_disconnected(market)
            else:
                await self._mark_disconnected(market)

            if self._stopped or self._market_stopped[market]:
                break

            established = self._connected_at.get(market)
            if established is not None and time.monotonic() - established >= WS_STABLE_SECONDS:
                attempts = 0
            delay = self._backoff_delay(attempts)
            attempts += 1
            logger.info(f"[WS:binance:{market}] reconnect attempt {attempts} in {delay:.1f}s")
            await asyncio.sleep(delay)

    async def _spot_session(self):
        url = ENDPOINTS[Exchange.BINANCE].ws
        async with self._http.ws_connect(url, autoping=True, heartbeat=WS_HEARTBEAT, proxy=self._ws_proxy()) as ws:
            await ws.send_json(self._build_subscribe_request())

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_spot_message(msg.json())
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break

    async def _futures_session(self):
        listen_key = await self._create_listen_key()
        refresh_task = asyncio.create_task(self._refresh_listen_key(listen_key))

        try:
            url = f"{ENDPOINTS[Exchange.BINANCE].futures_ws}{listen_key}"
            async with self._http.ws_connect(url, autoping=True, heartbeat=WS_HEARTBEAT, proxy=self._ws_proxy()) as ws:
                await self._mark_connected("futures")

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle_futures_message(msg.json())
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
        finally:
            refresh_task.cancel()
            try:
                await refresh_task
            except (asyncio.CancelledError, Exception):
                pass

    async def _mark_connected(self, market: str):
        self._connected_at[market] = time.monotonic()
        was_empty = not self._connected_markets
        self._connected_markets.add(market)
        logger.info(f"[WS:binance:{market}] connected key={self._api_key_id}")
        if was_empty:
            await self._on_status(self._api_key_id, True)

    async def _mark_disconnected(self, market: str):
        self._connected_markets.discard(market)
        if not self._connected_markets:
            await self._on_status(self._api_key_id, False)

    async def _handle_spot_message(self, data: dict):
        if "id" in data:
            if data.get("status") != 200:
                err = data.get("error") or {}
                raise self._subscribe_error(err.get("code", 0), err.get("msg", ""))
            await self._mark_connected("spot")
            return

        event = data.get("event") or {}
        if event.get("e") == self._SPOT_EVENT and event.get("x") == self._TRADE_EXEC_TYPE:
            await self._emit_trade(self._parse_event(event, MarketType.SPOT))

    async def _handle_futures_message(self, data: dict):
        if data.get("e") != self._FUTURES_EVENT:
            return

        o = data.get("o") or {}
        if o.get("x") == self._TRADE_EXEC_TYPE:
            await self._emit_trade(self._parse_event(o, MarketType.FUTURES))

    def _build_subscribe_request(self):
        params = {
            "apiKey": self._creds.api_key,
            "recvWindow": self._RECV_WINDOW,
            "timestamp": int(time.time() * 1000)
        }
        query = "&".join(f"{k}={params[k]}" for k in sorted(params))
        signature = hmac.new(self._creds.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        return {
            "id": str(uuid4()),
            "method": self._SUBSCRIBE_METHOD,
            "params": {**params, "signature": signature}
        }

    async def _create_listen_key(self):
        url = f"{ENDPOINTS[Exchange.BINANCE].futures_url}{self._FUTURES_LISTEN_KEY_PATH}"
        headers = {"X-MBX-APIKEY": self._creds.api_key}

        try:
            data = await self._executor.request(
                "POST", lambda: SignedRequest(url=url, headers=headers), self._POOL_FUT, weight=1
            )
        except WS_AUTH_FATAL as e:
            raise WSAuthFatalError(str(e.detail))

        if isinstance(data, dict):
            if data.get("listenKey"):
                return data["listenKey"]
            raise self._subscribe_error(data.get("code", 0), data.get("msg", ""))
        raise ConnectionError("Binance futures listenKey: empty response")

    async def _refresh_listen_key(self, listen_key: str):
        url = f"{ENDPOINTS[Exchange.BINANCE].futures_url}{self._FUTURES_LISTEN_KEY_PATH}?listenKey={listen_key}"
        headers = {"X-MBX-APIKEY": self._creds.api_key}

        while not self._stopped:
            await asyncio.sleep(self._LISTEN_KEY_REFRESH_SECONDS)
            try:
                await self._executor.request(
                    "PUT", lambda: SignedRequest(url=url, headers=headers), self._POOL_FUT, weight=1
                )
            except Exception as e:
                logger.warning(f"[WS:binance:futures] listenKey refresh error: {e}")

    @staticmethod
    def _subscribe_error(code: int, msg: str):
        exc = BinanceErrors.parse(code, msg)
        if isinstance(exc, (*WS_AUTH_FATAL, RateLimitError, ExchangeUnavailableError)):
            return WSAuthFatalError(str(exc.detail))
        return exc

    @staticmethod
    def _parse_event(d: dict, mt: MarketType):
        return NormalizedTrade(
            id=str(d["t"]),
            exchange=Exchange.BINANCE,
            market_type=mt,
            symbol=d["s"],
            time=from_ms(d["T"]),
            price=dec(d["L"]),
            quantity=dec(d["l"]),
            side=TradeSide.BUY if d["S"] == "BUY" else TradeSide.SELL,
            fee=dec_opt(d.get("n")),
            fee_asset=d.get("N"),
            order_id=str(d["i"]),
            realized_pnl=dec_opt(d.get("rp")),
            is_maker=d.get("m"),
            quote_qty=dec_opt(d.get("Y")),
            position_side=d.get("ps")
        )
