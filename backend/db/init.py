import asyncio
from pathlib import Path

import aiohttp
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from db.seed import seed_demo_data
from db.session import SessionFactory, engine
from domain.config import get_config
from utils.logger import logger

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ALEMBIC_INI = str(_BACKEND_DIR / "alembic.ini")
_SCRIPT_LOCATION = str(_BACKEND_DIR / "migrations")

_KLINES_COMPRESSION = (
    "ALTER TABLE market_klines SET (timescaledb.compress, "
    "timescaledb.compress_segmentby = 'exchange, market_type, symbol')"
)
_KLINES_COMPRESSION_POLICY = "SELECT add_compression_policy('market_klines', INTERVAL '7 days', if_not_exists => TRUE)"
_KLINES_RETENTION_POLICY = "SELECT add_retention_policy('market_klines', INTERVAL '12 months', if_not_exists => TRUE)"
_SETUPS_RETENTION_POLICY = "SELECT add_retention_policy('market_setups', INTERVAL '12 months', if_not_exists => TRUE)"

def _run_alembic_upgrade() -> None:
    cfg = Config(_ALEMBIC_INI)
    cfg.set_main_option("script_location", _SCRIPT_LOCATION)
    command.upgrade(cfg, "head")

async def _trades_exists() -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT to_regclass('public.trades')"))
        return result.scalar() is not None

async def _ensure_timescale() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
        await conn.execute(text(
            "SELECT create_hypertable('trades', 'time', if_not_exists => TRUE, migrate_data => TRUE)"
        ))
        for table in ("market_klines", "market_setups"):
            if (await conn.execute(text(f"SELECT to_regclass('public.{table}')"))).scalar() is not None:
                await conn.execute(text(
                    f"SELECT create_hypertable('{table}', 'time', if_not_exists => TRUE, migrate_data => TRUE)"
                ))
        await conn.commit()

    auto = await engine.connect()
    try:
        auto = await auto.execution_options(isolation_level="AUTOCOMMIT")
        if (await auto.execute(text("SELECT to_regclass('public.market_klines')"))).scalar() is not None:
            await auto.execute(text(_KLINES_COMPRESSION))
            await auto.execute(text(_KLINES_COMPRESSION_POLICY))
            await auto.execute(text(_KLINES_RETENTION_POLICY))
        if (await auto.execute(text("SELECT to_regclass('public.market_setups')"))).scalar() is not None:
            await auto.execute(text(_SETUPS_RETENTION_POLICY))
    finally:
        await auto.close()

async def init_db(http: aiohttp.ClientSession) -> None:
    await asyncio.to_thread(_run_alembic_upgrade)
    logger.info("Migrations applied (alembic upgrade head)")

    if not await _trades_exists():
        logger.warning(
            "[init] 'trades' table not found — schema is empty. Bootstrap with: "
            "`alembic revision --autogenerate -m baseline` (then restart backend)"
        )
        return

    await _ensure_timescale()
    logger.info("TimescaleDB extension + hypertables + policies ensured")

    if get_config().seed_demo_data:
        async with SessionFactory() as session:
            if await seed_demo_data(session, http):
                logger.info("Demo data seeded")
            else:
                logger.info("Demo data already present — seed skipped")
