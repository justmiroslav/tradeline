import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from domain.config import get_config

engine = create_async_engine(get_config().database_url, echo=False, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def warm_pool(connections: int = 8) -> None:
    async def ping() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    await asyncio.gather(*[ping() for _ in range(connections)], return_exceptions=True)
