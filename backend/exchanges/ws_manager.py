import aiohttp, asyncio

from time import monotonic
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.repositories.api_key import ApiKeyRepository
from domain.enums import Exchange
from domain.models import ApiKey
from shared.security import decrypt
from utils.logger import logger

from .binance import BinanceWSHandler
from .bitget import BitgetWSHandler
from .bybit import BybitWSHandler
from .gateway import ExchangeGateway
from .okx import OKXWSHandler
from .proxy_pool import ProxyRouter
from .types import DecryptedCredentials

_REGISTRY = {
    Exchange.BINANCE: BinanceWSHandler,
    Exchange.BYBIT: BybitWSHandler,
    Exchange.BITGET: BitgetWSHandler,
    Exchange.OKX: OKXWSHandler
}

class WebSocketManager:
    _ROLLING_RECONNECT_SECONDS = 8 * 3600
    _ROLLING_CHECK_INTERVAL = 60

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], ws_http: aiohttp.ClientSession, gateway: ExchangeGateway, on_trade, proxy_router: ProxyRouter | None = None):
        self._sf = session_factory
        self._ws_http = ws_http
        self._gateway = gateway
        self._on_trade = on_trade
        self._proxy_router = proxy_router
        self._handlers = {}
        self._tasks = {}
        self._started_at = {}
        self._locks = {}
        self._rolling_task = None

    async def start_all(self):
        async with self._sf() as session:
            keys = await ApiKeyRepository(session).get_all_global()
        for key in keys:
            await self.connect(key)

        self._rolling_task = asyncio.create_task(self._rolling_loop())
        logger.info(f"[WSManager] started: ws={len(self._handlers)}")

    async def stop_all(self):
        if self._rolling_task:
            self._rolling_task.cancel()
            try:
                await self._rolling_task
            except asyncio.CancelledError:
                pass
            self._rolling_task = None

        for kid in list(self._tasks):
            await self.disconnect(kid)

    async def connect(self, api_key: ApiKey):
        async with self._lock_for(api_key.id):
            if api_key.last_error:
                logger.info(f"[WSManager] skipping {api_key.id} — last_error set, awaiting re-validation")
                return
            if api_key.id in self._handlers:
                return

            cls = _REGISTRY.get(api_key.exchange)
            if not cls:
                return

            creds = self._decrypt(api_key)
            handler = cls(
                creds=creds, http=self._ws_http,
                executor=self._gateway.executor(api_key.exchange),
                api_key_id=api_key.id, user_id=api_key.user_id,
                capabilities=api_key.capabilities,
                on_trade=self._on_trade, on_status=self._on_status,
                on_auth_fatal=self._on_auth_fatal
            )
            handler.attach_proxy_router(self._proxy_router)

            task = asyncio.create_task(handler.run())
            self._handlers[api_key.id] = handler
            self._tasks[api_key.id] = task
            self._started_at[api_key.id] = monotonic()
            task.add_done_callback(lambda t, k=api_key.id: self._on_task_done(k, t))

    async def disconnect(self, api_key_id: UUID, persist_status: bool = True):
        async with self._lock_for(api_key_id):
            handler = self._handlers.pop(api_key_id, None)
            task = self._tasks.pop(api_key_id, None)
            self._started_at.pop(api_key_id, None)

            if handler:
                await handler.stop()
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if handler is not None and persist_status:
                await self._on_status(api_key_id, False)

    def is_live(self, api_key_id: UUID) -> bool:
        task = self._tasks.get(api_key_id)
        return task is not None and not task.done()

    def _lock_for(self, key_id: UUID) -> asyncio.Lock:
        lock = self._locks.get(key_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key_id] = lock
        return lock

    def _on_task_done(self, api_key_id: UUID, task: asyncio.Task):
        asyncio.create_task(self._cleanup_finished(api_key_id, task))

    async def _cleanup_finished(self, api_key_id: UUID, task: asyncio.Task):
        async with self._lock_for(api_key_id):
            if self._tasks.get(api_key_id) is not task:
                return

            self._handlers.pop(api_key_id, None)
            self._tasks.pop(api_key_id, None)
            self._started_at.pop(api_key_id, None)

    async def _rolling_loop(self):
        try:
            while True:
                await asyncio.sleep(self._ROLLING_CHECK_INTERVAL)
                now = monotonic()
                stale = [kid for kid, t in self._started_at.items() if now - t > self._ROLLING_RECONNECT_SECONDS]

                for kid in stale:
                    async with self._sf() as session:
                        key = await ApiKeyRepository(session).get_global(kid)
                    if key is None:
                        continue

                    logger.info(f"[WSManager] rolling 8h reconnect for key={kid} ({key.exchange.value})")
                    await self.disconnect(kid)
                    await self.connect(key)
        except asyncio.CancelledError:
            return

    @staticmethod
    def _decrypt(api_key: ApiKey) -> DecryptedCredentials:
        return DecryptedCredentials(
            api_key=decrypt(api_key.api_key_encrypted),
            api_secret=decrypt(api_key.api_secret_encrypted),
            passphrase=decrypt(api_key.passphrase_encrypted) if api_key.passphrase_encrypted else None
        )

    async def _on_status(self, api_key_id: UUID, connected: bool):
        try:
            async with self._sf() as session:
                await ApiKeyRepository(session).update_ws_status(api_key_id, connected)
        except Exception as e:
            logger.warning(f"[WSManager] status update error: {e}")

    async def _on_auth_fatal(self, api_key_id: UUID, message: str):
        try:
            async with self._sf() as session:
                await ApiKeyRepository(session).set_last_error(api_key_id, message[:512])
        except Exception as e:
            logger.warning(f"[WSManager] auth-fatal recording error: {e}")
