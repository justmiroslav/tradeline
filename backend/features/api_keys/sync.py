from datetime import datetime
from time import monotonic

from db.repositories.event import EventRepository
from db.repositories.market import MarketRepository
from db.repositories.trade import TradeRepository
from db.session import SessionFactory
from domain.enums import PlanTier
from domain.models import ApiKey
from exchanges.client import BaseExchangeClient
from exchanges.helpers import FETCH_ERRORS
from exchanges.symbols_cache import SymbolCache
from exchanges.ws_manager import WebSocketManager
from features.positions.service import PositionsService
from features.trades.ingester import TradeIngester
from features.trades.service import TradeService
from shared.exceptions import ExchangeError
from utils.logger import brief, logger

async def _reconcile_incomplete(key: ApiKey, client: BaseExchangeClient, ingester: TradeIngester) -> None:
    try:
        balances = await client.fetch_spot_balances()
    except NotImplementedError:
        return
    except (*FETCH_ERRORS, ExchangeError) as e:
        logger.warning(f"[api-keys] balance reconcile skipped key={key.id}: {brief(e)}")
        return
    async with SessionFactory() as session:
        marked = await PositionsService(session).reconcile_incomplete(key.id, balances)
    if marked:
        ingester.touch(key.user_id)
        logger.info(f"[api-keys] {key.exchange.value} key={key.id}: {marked} positions marked incomplete")

async def run_initial_sync(ws_mgr: WebSocketManager, ingester: TradeIngester, cache: SymbolCache, key: ApiKey,
                           client: BaseExchangeClient, tier: PlanTier, progress: dict,
                           since: datetime | None = None) -> None:
    started = monotonic()
    progress[key.id] = {"state": "syncing"}
    ingester.begin_backfill(key.id)
    await ws_mgr.connect(key)

    try:
        async with SessionFactory() as session:
            inserted = await TradeService(session, cache).sync(key, client, tier, since)
            symbols = await TradeRepository(session).distinct_symbols(key.id)
            await MarketRepository(session).activate(key.exchange, symbols)

        if inserted:
            await ingester.apply_backfill(key.user_id, key.id, inserted)
        ingester.end_backfill(key.id)

        if "spot" in key.capabilities:
            await _reconcile_incomplete(key, client, ingester)

        async with SessionFactory() as session:
            await MarketRepository(session).link_position_setups(key.user_id)
            await EventRepository(session).record("sync_done", key.user_id, {
                "exchange": key.exchange.value, "trades": len(inserted),
                "symbols": len(symbols), "seconds": round(monotonic() - started, 1)
            })
        ingester.touch(key.user_id)

        progress[key.id] = {"state": "done"}
        ingester.notify_synced(key.user_id, key.id)
        logger.info(
            f"[api-keys] sync done: {key.exchange.value} key={key.id} "
            f"+{len(inserted)} trades across {len(symbols)} symbols in {monotonic() - started:.1f}s"
        )
    except Exception as e:
        ingester.forget(key.id)
        await ws_mgr.disconnect(key.id)
        logger.warning(f"[api-keys] sync failed: {key.exchange.value} key={key.id}: {brief(e)}")
        progress[key.id] = {"state": "error"}
