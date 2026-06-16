from domain.enums import Exchange

from .rate_limiter import TokenBucket
from .types import BucketSpec

class ProxyRouter:
    def __init__(self, proxies: list[str], rate_configs: dict[Exchange, dict[str, BucketSpec]]):
        self._proxies = proxies
        self._configs = rate_configs
        self._lanes: dict[tuple[Exchange, str], list[TokenBucket]] = {}
        self._cursor: dict[tuple[Exchange, str], int] = {}
        self._ws_cursor = 0

    @property
    def enabled(self) -> bool:
        return bool(self._proxies)

    async def acquire(self, exchange: Exchange, pool: str, weight: float = 1.0) -> tuple[str | None, TokenBucket]:
        spec = self._spec(exchange, pool)
        slots = self._slots(exchange, pool)
        if not self._proxies:
            await slots[0].acquire(weight)
            return None, slots[0]

        key = (exchange, pool)
        start = self._cursor.get(key, 0)
        self._cursor[key] = start + 1

        if not spec.per_ip:
            await slots[0].acquire(weight)
            return self._proxies[start % len(self._proxies)], slots[0]

        count = len(slots)
        for i in range(count):
            idx = (start + i) % count
            if await slots[idx].try_acquire(weight):
                return self._proxies[idx], slots[idx]

        idx = start % count
        await slots[idx].acquire(weight)
        return self._proxies[idx], slots[idx]

    def next_ws(self) -> str | None:
        if not self._proxies:
            return None
        cursor = self._ws_cursor
        self._ws_cursor += 1
        return self._proxies[cursor % len(self._proxies)]

    def snapshot(self) -> dict[str, int]:
        return {f"{exchange.value}:{pool}": len(slots) for (exchange, pool), slots in self._lanes.items()}

    def _spec(self, exchange: Exchange, pool: str) -> BucketSpec:
        return self._configs[exchange][pool]

    def _slots(self, exchange: Exchange, pool: str) -> list[TokenBucket]:
        key = (exchange, pool)
        slots = self._lanes.get(key)
        if slots is None:
            spec = self._spec(exchange, pool)
            lanes = len(self._proxies) if spec.per_ip and self._proxies else 1
            slots = [TokenBucket(spec) for _ in range(lanes)]
            self._lanes[key] = slots
        return slots
