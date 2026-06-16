import time, asyncio

from .types import BucketSpec

class TokenBucket:
    def __init__(self, spec: BucketSpec):
        self.spec = spec
        self._tokens = min(float(spec.capacity), spec.refill_per_sec * 3.0)
        self._last = time.monotonic()
        self._lock = asyncio.Lock()
        self._penalty_until = 0.0

    async def acquire(self, weight: float = 1.0):
        while True:
            async with self._lock:
                wait = self._refill_take(weight)
                if wait is None:
                    return
            await asyncio.sleep(wait)

    async def try_acquire(self, weight: float = 1.0) -> bool:
        async with self._lock:
            return self._refill_take(weight) is None

    def _refill_take(self, weight: float) -> float | None:
        now = time.monotonic()
        if now < self._penalty_until:
            return self._penalty_until - now

        elapsed = now - self._last
        self._tokens = min(float(self.spec.capacity), self._tokens + elapsed * self.spec.refill_per_sec)
        self._last = now
        if self._tokens >= weight:
            self._tokens -= weight
            return None

        deficit = weight - self._tokens
        return max(deficit / self.spec.refill_per_sec, 0.001) if self.spec.refill_per_sec > 0 else 1.0

    def snap(self, remaining: float):
        self._tokens = max(0.0, min(float(self.spec.capacity), float(remaining)))
        self._last = time.monotonic()

    def penalize(self, seconds: float):
        self._penalty_until = max(self._penalty_until, time.monotonic() + max(seconds, 0.0))

    def observe(self, headers):
        spec = self.spec
        if spec.header_remaining_key:
            raw = headers.get(spec.header_remaining_key)
            if raw is not None:
                try:
                    self.snap(int(raw))
                    return
                except (ValueError, TypeError):
                    pass

        if spec.header_used_key:
            raw = headers.get(spec.header_used_key)
            if raw is not None:
                try:
                    self._tokens = max(0.0, min(self._tokens, float(spec.capacity - int(raw))))
                    self._last = time.monotonic()
                except (ValueError, TypeError):
                    pass
