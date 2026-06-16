import aiohttp

from abc import ABC, abstractmethod
from uuid import UUID

from utils.logger import logger

from ..config import BACKOFF_BASE, BACKOFF_CAP, BACKOFF_FLOOR
from ..helpers import expo_jitter
from ..http_executor import RequestExecutor
from ..proxy_pool import ProxyRouter
from ..types import DecryptedCredentials, NormalizedTrade

class BaseWSHandler(ABC):
    exchange = None

    def __init__(self, creds: DecryptedCredentials, http: aiohttp.ClientSession, executor: RequestExecutor, api_key_id: UUID, user_id: UUID, capabilities: list[str], on_trade, on_status, on_auth_fatal):
        self._creds = creds
        self._http = http
        self._executor = executor
        self._api_key_id = api_key_id
        self._user_id = user_id
        self._capabilities = capabilities
        self._on_trade = on_trade
        self._on_status = on_status
        self._on_auth_fatal = on_auth_fatal
        self._ws = None
        self._stopped = False
        self._proxy_router: ProxyRouter | None = None

    def attach_proxy_router(self, router: ProxyRouter | None) -> None:
        self._proxy_router = router

    def _ws_proxy(self) -> str | None:
        return self._proxy_router.next_ws() if self._proxy_router is not None else None

    @abstractmethod
    async def run(self): ...

    @staticmethod
    def _backoff_delay(attempts: int) -> float:
        return expo_jitter(attempts, base=BACKOFF_BASE, cap=BACKOFF_CAP, floor=BACKOFF_FLOOR)

    async def stop(self):
        self._stopped = True
        if self._ws and not self._ws.closed:
            await self._ws.close()

    async def _emit_trade(self, trade: NormalizedTrade):
        try:
            await self._on_trade(self._user_id, self._api_key_id, trade)
        except Exception as e:
            logger.warning(f"[WS:{self.exchange.value}] trade callback error: {e}")

    async def _notify_auth_fatal(self, message: str):
        try:
            await self._on_auth_fatal(self._api_key_id, message)
        except Exception as e:
            logger.warning(f"[WS:{self.exchange.value}] auth-fatal callback error: {e}")
