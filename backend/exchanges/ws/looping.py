import aiohttp, asyncio

from abc import abstractmethod
from time import monotonic

from utils.logger import logger

from ..config import WS_HEARTBEAT, WS_STABLE_SECONDS
from ..errors import WSAuthFatalError
from .base import BaseWSHandler

class LoopingWSHandler(BaseWSHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attempts = 0

    async def _keepalive(self):
        return

    async def _keepalive_loop(self):
        try:
            await self._keepalive()
        except Exception as e:
            logger.warning(f"[WS:{self.exchange.value}] keepalive died: {e}")
            if self._ws is not None and not self._ws.closed:
                try:
                    await self._ws.close()
                except Exception:
                    pass

    async def run(self):
        while not self._stopped:
            ka_task = None
            connected_at = None

            try:
                async with self._http.ws_connect(self._ws_url(), heartbeat=WS_HEARTBEAT, proxy=self._ws_proxy()) as ws:
                    self._ws = ws
                    await self._authenticate()
                    await self._subscribe()
                    ka_task = asyncio.create_task(self._keepalive_loop())
                    connected_at = monotonic()

                    await self._on_status(self._api_key_id, True)
                    logger.info(f"[WS:{self.exchange.value}] connected key={self._api_key_id}")
                    await self._listen()
            except WSAuthFatalError as e:
                logger.error(
                    f"[WS:{self.exchange.value}] fatal auth error for key={self._api_key_id}: {e} — "
                    "stopping reconnects (key needs to be re-validated)"
                )
                await self._notify_auth_fatal(str(e))
                self._stopped = True
            except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError) as e:
                logger.warning(f"[WS:{self.exchange.value}] error: {e}")
            except asyncio.CancelledError:
                break
            finally:
                if ka_task:
                    ka_task.cancel()
                self._ws = None
                await self._on_status(self._api_key_id, False)

            if self._stopped:
                break

            if connected_at is not None and monotonic() - connected_at >= WS_STABLE_SECONDS:
                self._attempts = 0
            delay = self._backoff_delay(self._attempts)
            self._attempts += 1
            logger.info(f"[WS:{self.exchange.value}] reconnect attempt {self._attempts} in {delay:.1f}s")
            await asyncio.sleep(delay)

    async def _listen(self):
        async for msg in self._ws:
            if self._stopped:
                break
            if msg.type == aiohttp.WSMsgType.TEXT:
                if await self._handle_ping(msg):
                    continue
                await self._on_message(msg.json())
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                break

    async def _handle_ping(self, msg: aiohttp.WSMessage):
        if msg.data == "ping":
            await self._ws.send_str("pong")
            return True
        return False

    @abstractmethod
    def _ws_url(self) -> str: ...

    @abstractmethod
    async def _authenticate(self): ...

    @abstractmethod
    async def _subscribe(self): ...

    @abstractmethod
    async def _on_message(self, data: dict): ...
