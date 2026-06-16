import hmac, time, aiohttp, base64, asyncio, hashlib

from abc import abstractmethod

from domain.enums import MarketType

from ..errors import WS_AUTH_FATAL, ExchangeErrors, WSAuthFatalError
from .looping import LoopingWSHandler

class OKStyleWSHandler(LoopingWSHandler):
    _AUTH_PATH: str
    _PING_INTERVAL: int
    _INST_MAP: dict[MarketType, str]
    _ERRORS: type[ExchangeErrors]
    _CHANNEL = "orders"
    _FILLED_STATES = frozenset({"filled", "partially_filled"})
    _SUBSCRIBE_EXTRA = {}

    async def _authenticate(self):
        ts = str(int(time.time()))
        sign = base64.b64encode(
            hmac.new(self._creds.api_secret.encode(),
                     (ts + "GET" + self._AUTH_PATH).encode(),
                     hashlib.sha256).digest()
        ).decode()

        await self._ws.send_json({
            "op": "login",
            "args": [{
                "apiKey": self._creds.api_key,
                "passphrase": self._creds.passphrase or "",
                "timestamp": ts,
                "sign": sign
            }]
        })

        resp = await self._ws.receive_json()
        code = str(resp.get("code", ""))
        if code == "0":
            return

        msg = resp.get("msg", "") or str(resp)
        exc = self._ERRORS.parse(code, msg)
        if isinstance(exc, WS_AUTH_FATAL):
            raise WSAuthFatalError(str(exc.detail))
        raise ConnectionError(f"{self.exchange.value} auth failed (code={code}): {msg}")

    async def _subscribe(self):
        args = []
        for mt, inst in self._INST_MAP.items():
            cap = "spot" if mt == MarketType.SPOT else "futures"
            if cap in self._capabilities:
                args.append({"channel": self._CHANNEL, "instType": inst, **self._SUBSCRIBE_EXTRA})

        if args:
            await self._ws.send_json({"op": "subscribe", "args": args})

    async def _keepalive(self):
        while not self._stopped:
            await asyncio.sleep(self._PING_INTERVAL)
            if self._ws is None or self._ws.closed:
                return
            try:
                await self._ws.send_str("ping")
            except (aiohttp.ClientError, ConnectionError):
                return

    async def _handle_ping(self, msg: aiohttp.WSMessage):
        if msg.data == "ping":
            await self._ws.send_str("pong")
            return True
        if msg.data == "pong":
            return True
        return False

    async def _on_message(self, data: dict):
        arg = data.get("arg", {})
        if arg.get("channel") != self._CHANNEL:
            return

        inst_type = str(arg.get("instType", "")).upper()
        mt = next((m for m, inst in self._INST_MAP.items() if inst.upper() == inst_type), None)
        if mt is None:
            return

        for row in data.get("data", []):
            state = str(row.get("state") or row.get("status") or "").lower()
            if state not in self._FILLED_STATES:
                continue
            if not row.get("tradeId"):
                continue
            await self._emit_trade(self._parse_ws_fill(row, mt))

    @abstractmethod
    def _parse_ws_fill(self, row: dict, mt: MarketType): ...
