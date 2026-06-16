from collections.abc import Iterator

from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository:
    _BATCH_ROWS = 1000

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _one(self, stmt):
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _all(self, stmt) -> list:
        return list((await self.session.execute(stmt)).scalars().all())

    async def _count(self, stmt) -> int:
        return (await self.session.execute(stmt)).scalar_one()

    @classmethod
    def batches(cls, rows: list) -> Iterator[list]:
        for i in range(0, len(rows), cls._BATCH_ROWS):
            yield rows[i:i + cls._BATCH_ROWS]
