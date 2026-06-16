import asyncio

from abc import ABC, abstractmethod
from typing import Optional

from utils.logger import brief, logger

class PeriodicWorker(ABC):
    _TICK_SECONDS = 60
    _FIRST_DELAY = 0
    _LABEL = "Worker"

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._stopped = False

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopped = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _warmup(self) -> None:
        return

    @abstractmethod
    async def _tick(self) -> None: ...

    async def _run(self) -> None:
        await self._warmup()
        if self._FIRST_DELAY:
            await asyncio.sleep(self._FIRST_DELAY)
        while not self._stopped:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[{self._LABEL}] tick error: {brief(e)}")
            await asyncio.sleep(self._TICK_SECONDS)
