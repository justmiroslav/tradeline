import hmac, time, aiohttp, asyncio, hashlib

from domain.enums import Exchange, MarketType

from ..config import ENDPOINTS
from ..errors import WS_AUTH_FATAL, WSAuthFatalError
from ..ws import LoopingWSHandler
from .errors import BybitErrors
from .rest import parse_execution

class BybitWSHandler(LoopingWSHandler):
    exchange = Exchange.BYBIT

    _PING_INTERVAL = 20

    def _ws_url(self) -> str:
        return ENDPOINTS[Exchange.BYBIT].ws

    async def _authenticate(self):
        expires = str(int(time.time() * 1000) + 10_000)
        sign = hmac.new(self._creds.api_secret.encode(), f"GET/realtime{expires}".encode(), hashlib.sha256).hexdigest()

        await self._ws.send_json({"op": "auth", "args": [self._creds.api_key, expires, sign]})

        resp = await self._ws.receive_json()
        if not resp.get("success"):
            code = resp.get("ret_code") or resp.get("retCode") or 0
            msg = resp.get("ret_msg") or resp.get("retMsg") or str(resp)
            exc = BybitErrors.parse(code, msg)
            if isinstance(exc, WS_AUTH_FATAL):
                raise WSAuthFatalError(str(exc.detail))
            raise ConnectionError(str(exc.detail))

    async def _subscribe(self):
        topics = []
        if "spot" in self._capabilities:
            topics.append("execution.spot")
        if "futures" in self._capabilities:
            topics.append("execution.linear")
        if topics:
            await self._ws.send_json({"op": "subscribe", "args": topics})

    async def _keepalive(self):
        while not self._stopped:
            await asyncio.sleep(self._PING_INTERVAL)
            if self._ws is None or self._ws.closed:
                return
            try:
                await self._ws.send_json({"op": "ping"})
            except (aiohttp.ClientError, ConnectionError):
                return

    async def _handle_ping(self, msg: aiohttp.WSMessage):
        try:
            data = msg.json()
        except ValueError:
            return False
        if data.get("op") == "ping":
            await self._ws.send_json({"op": "pong"})
            return True
        return False

    async def _on_message(self, data: dict):
        if not str(data.get("topic", "")).startswith("execution"):
            return

        for row in data.get("data", []):
            if row.get("execType") != "Trade":
                continue
            cat = row.get("category", "")
            if cat == "spot":
                mt = MarketType.SPOT
            elif cat == "linear":
                mt = MarketType.FUTURES
            else:
                continue
            await self._emit_trade(parse_execution(row, mt))
