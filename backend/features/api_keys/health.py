import asyncio

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.repositories.api_key import ApiKeyRepository
from db.repositories.user import UserRepository
from domain.models import ApiKey
from exchanges.gateway import ExchangeGateway
from exchanges.helpers import FETCH_ERRORS
from exchanges.symbols_cache import SymbolCache
from exchanges.ws_manager import WebSocketManager
from features.api_keys.service import RECHECK_INTERVAL, SUSPENDED_BY_PLAN, client_for_key, confirm_key_valid, ensure_ip_restricted
from features.api_keys.sync import run_initial_sync
from features.trades.ingester import TradeIngester
from shared.exceptions import ExchangeError, ExchangeUnavailableError, RateLimitError
from shared.worker import PeriodicWorker
from utils.logger import brief, logger

class KeyHealthWorker(PeriodicWorker):
    _TICK_SECONDS = 30
    _FIRST_DELAY = 15
    _LABEL = "KeyHealthWorker"
    _BATCH = 5

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], ws_manager: WebSocketManager,
                 gateway: ExchangeGateway, ingester: TradeIngester, cache: SymbolCache, progress: dict):
        super().__init__()
        self._sf = session_factory
        self._ws = ws_manager
        self._gateway = gateway
        self._ingester = ingester
        self._cache = cache
        self._progress = progress
        self._recoveries: set[asyncio.Task] = set()

    async def _warmup(self) -> None:
        await self._rolling_start()

    async def _rolling_start(self) -> None:
        async with self._sf() as session:
            keys = await ApiKeyRepository(session).get_all_global()

        base = datetime.now(timezone.utc)
        async with self._sf() as session:
            repo = ApiKeyRepository(session)
            for key in keys:
                await repo.set_next_check(key.id, base)

    async def _tick(self) -> None:
        async with self._sf() as session:
            due = await ApiKeyRepository(session).due_for_check(self._BATCH)
        await asyncio.gather(*[self._check_guarded(key) for key in due])

    async def _check_guarded(self, key: ApiKey) -> None:
        try:
            await self._check_one(key)
        except Exception as e:
            logger.warning(f"[KeyHealthWorker] {key.id} check failed: {brief(e)}")

    async def _check_one(self, key: ApiKey) -> None:
        if key.last_error == SUSPENDED_BY_PLAN:
            async with self._sf() as session:
                await ApiKeyRepository(session).set_next_check(key.id, datetime.now(timezone.utc) + RECHECK_INTERVAL)
            return

        client = client_for_key(self._gateway, key)

        try:
            caps = await client.validate_credentials()
            ensure_ip_restricted(caps, key.exchange)
        except (RateLimitError, ExchangeUnavailableError, *FETCH_ERRORS) as e:
            logger.info(f"[KeyHealthWorker] {key.exchange.value} key={key.id} check postponed (transient): {brief(e)}")
            async with self._sf() as session:
                await ApiKeyRepository(session).set_next_check(key.id, datetime.now(timezone.utc) + RECHECK_INTERVAL)
            return
        except ExchangeError as e:
            logger.info(f"[KeyHealthWorker] {key.id} ({key.exchange.value}) invalid: {e}")
            async with self._sf() as session:
                await ApiKeyRepository(session).mark_checked(key.id, datetime.now(timezone.utc) + RECHECK_INTERVAL, str(e.detail)[:512])
            if self._ws.is_live(key.id):
                await self._ws.disconnect(key.id)
            return

        recovering = key.last_error is not None
        async with self._sf() as session:
            fresh = await confirm_key_valid(session, key, caps)
            user = await UserRepository(session).get_by_id(fresh.user_id) if fresh else None
        if fresh is None or user is None:
            return

        if not recovering and self._ws.is_live(key.id):
            return

        reason = "recovered after error" if recovering else "ws not live"
        since = key.last_error_at - RECHECK_INTERVAL if key.last_error_at else None
        logger.info(f"[KeyHealthWorker] {key.exchange.value} key={key.id} {reason} — starting resync")
        task = asyncio.create_task(
            run_initial_sync(self._ws, self._ingester, self._cache, fresh, client, user.plan, self._progress, since)
        )
        self._recoveries.add(task)
        task.add_done_callback(self._recoveries.discard)
