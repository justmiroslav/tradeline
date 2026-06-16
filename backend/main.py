import asyncio

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.init import init_db
from db.seed import DEMO_USER_ID
from db.session import SessionFactory, warm_pool
from domain.config import get_config
from exchanges.config import RATE_CONFIGS
from exchanges.gateway import ExchangeGateway
from exchanges.proxy_pool import ProxyRouter
from exchanges.symbols_cache import SymbolCache
from exchanges.ws_manager import WebSocketManager
from features.analytics.cache import AnalyticsCache
from features.api_keys.health import KeyHealthWorker
from features.market.worker import MarketTickerWorker
from features.market_setups.worker import MarketSetupWorker
from features.trades.ingester import TradeIngester
from features.email.sender import LogEmailSender, ResendEmailSender
from features.auth.router import router as auth_router
from features.api_keys.router import router as api_keys_router
from features.trades.router import router as trades_router
from features.plans.router import router as plans_router
from features.analytics.router import router as analytics_router
from features.positions.router import router as positions_router
from features.stream.router import router as stream_router
from features.ai.router import router as ai_router
from features.market.router import router as market_router
from features.billing.router import router as billing_router
from features.reviews.router import router as reviews_router
from features.telegram.bot import TelegramBot
from shared.deps import get_current_user
from shared.event_bus import EventBus
from shared.exceptions import register_error_handlers
from shared.http import create_rest_session, create_ws_session
from shared.telegram import TelegramClient
from shared.rate_limit import DEFAULT_RULES, RateLimiter, RateLimitMiddleware
from utils.logger import logger

@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.rest_http = create_rest_session()
    application.state.ws_http = create_ws_session()
    await init_db(application.state.rest_http)

    config = get_config()
    application.state.proxy_router = ProxyRouter(config.proxy_pool, RATE_CONFIGS)
    application.state.event_bus = EventBus()
    application.state.sync_progress = {}
    application.state.email_sender = (
        ResendEmailSender(application.state.rest_http, config.resend_api_key, config.email_from)
        if config.resend_api_key else LogEmailSender()
    )
    application.state.analytics_cache = AnalyticsCache()
    application.state.gateway = ExchangeGateway(application.state.rest_http, application.state.proxy_router)
    application.state.symbol_cache = SymbolCache(application.state.gateway)
    application.state.trade_ingester = TradeIngester(
        SessionFactory, application.state.event_bus,
        application.state.analytics_cache.bump_append, application.state.analytics_cache.bump_invalidate
    )
    application.state.ws_manager = WebSocketManager(
        SessionFactory, application.state.ws_http, application.state.gateway, application.state.trade_ingester.add,
        application.state.proxy_router
    )
    application.state.key_health_worker = KeyHealthWorker(
        SessionFactory, application.state.ws_manager, application.state.gateway,
        application.state.trade_ingester, application.state.symbol_cache, application.state.sync_progress
    )
    application.state.market_setup_worker = MarketSetupWorker(
        SessionFactory, application.state.gateway, application.state.analytics_cache
    )
    application.state.market_ticker_worker = MarketTickerWorker(application.state.gateway)

    application.state.telegram = (
        TelegramClient(application.state.rest_http, config.telegram_bot_token,
                       config.telegram_owner_chat_id, config.telegram_review_chat_id)
        if config.telegram_enabled else None
    )
    application.state.telegram_bot = TelegramBot(SessionFactory, application.state.telegram) if application.state.telegram else None

    application.state.symbol_cache.start()
    application.state.trade_ingester.start()
    await application.state.ws_manager.start_all()
    application.state.key_health_worker.start()
    application.state.market_setup_worker.start()
    application.state.market_ticker_worker.start()
    if application.state.telegram_bot:
        application.state.telegram_bot.start()

    await warm_pool()
    if get_config().seed_demo_data:
        application.state.seed_rebuild_task = asyncio.create_task(application.state.trade_ingester.rebuild(DEMO_USER_ID))

    logger.info("Application started")
    yield

    if application.state.telegram_bot:
        await application.state.telegram_bot.stop()
    await application.state.market_ticker_worker.stop()
    await application.state.market_setup_worker.stop()
    await application.state.key_health_worker.stop()
    await application.state.ws_manager.stop_all()
    await application.state.trade_ingester.stop()
    await application.state.symbol_cache.stop()
    await application.state.rest_http.close()
    await application.state.ws_http.close()

    logger.info("Shutting down")

_docs_config = get_config()
app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if _docs_config.enable_docs else None,
    redoc_url="/redoc" if _docs_config.enable_docs else None,
    openapi_url="/openapi.json" if _docs_config.enable_docs else None
)
register_error_handlers(app)

app.add_middleware(
    RateLimitMiddleware,  # type: ignore[arg-type]
    limiter=RateLimiter(DEFAULT_RULES)
)
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=[get_config().frontend_url], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(trades_router)
app.include_router(plans_router)
app.include_router(analytics_router)
app.include_router(positions_router)
app.include_router(stream_router)
app.include_router(ai_router)
app.include_router(market_router)
app.include_router(billing_router)
app.include_router(reviews_router)

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.get("/info", dependencies=[Depends(get_current_user)])
async def info() -> dict:
    return {"whitelist_ips": get_config().proxy_ips}
