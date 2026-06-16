import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import UUID

from utils.logger import logger

class EventBus:
    _QUEUE_MAX = 100

    def __init__(self) -> None:
        self._subscribers: dict[UUID, set[asyncio.Queue]] = {}

    @asynccontextmanager
    async def subscribe(self, user_id: UUID) -> AsyncIterator[asyncio.Queue]:
        q = asyncio.Queue(maxsize=self._QUEUE_MAX)
        self._subscribers.setdefault(user_id, set()).add(q)
        try:
            yield q
        finally:
            subs = self._subscribers.get(user_id)
            if subs:
                subs.discard(q)
                if not subs:
                    self._subscribers.pop(user_id, None)

    def publish(self, user_id: UUID, event_type: str, payload: dict) -> None:
        subs = self._subscribers.get(user_id)
        if not subs:
            return
        envelope = {"type": event_type, "data": payload}
        evicted = 0
        for q in subs:
            try:
                q.put_nowait(envelope)
            except asyncio.QueueFull:
                q.get_nowait()
                q.put_nowait(envelope)
                evicted += 1
        if evicted:
            logger.warning(f"[EventBus] evicted oldest events for {evicted} slow subscriber(s) of user {user_id}")
