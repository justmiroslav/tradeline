import asyncio, aiohttp

from collections.abc import Callable

from domain.enums import Exchange
from utils.logger import brief, logger

from .errors import raise_for_status, retry_after_seconds
from .helpers import expo_jitter, proxy_label, qs
from .proxy_pool import ProxyRouter
from .types import SignedRequest

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=25, sock_connect=8, sock_read=20)

class RequestExecutor:
    _MAX_RETRIES = 3

    def __init__(self, exchange: Exchange, session: aiohttp.ClientSession, router: ProxyRouter):
        self._exchange = exchange
        self._session = session
        self._router = router

    async def request(self, method: str, build_request: Callable[[], SignedRequest], pool: str, weight: int = 1):
        last_exc = None

        for attempt in range(self._MAX_RETRIES):
            proxy, bucket = await self._router.acquire(self._exchange, pool, weight)
            req = build_request()

            try:
                async with self._session.request(method, req.url, headers=req.headers, data=req.body, proxy=proxy, timeout=_REQUEST_TIMEOUT) as r:
                    if r.status in (418, 429):
                        ra = retry_after_seconds(r)
                        floor = 60.0 if r.status == 418 else 1.0
                        penalty = max(ra if ra is not None else expo_jitter(attempt), floor)
                        bucket.penalize(penalty)
                        label = proxy_label(proxy)
                        logger.warning(
                            f"[{self._exchange.value}] rate limited (HTTP {r.status}) on pool={pool}"
                            f"{f' via {label}' if label else ''} — backing off {penalty:.1f}s, attempt {attempt + 1}/{self._MAX_RETRIES}"
                        )
                        if r.status == 429 and attempt + 1 < self._MAX_RETRIES:
                            continue
                        await raise_for_status(self._exchange, r)
                        return None

                    await raise_for_status(self._exchange, r)
                    bucket.observe(r.headers)
                    return await r.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exc = e
                if attempt + 1 < self._MAX_RETRIES:
                    delay = expo_jitter(attempt)
                    logger.warning(
                        f"[{self._exchange.value}] network error on pool={pool} ({brief(e, 120)}) — "
                        f"retry {attempt + 2}/{self._MAX_RETRIES} in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise

        if last_exc:
            raise last_exc

        return None

    async def get_public(self, base: str, path: str, pool: str, params: dict | None = None, weight: int = 1):
        query = qs(params)
        url = f"{base}{path}?{query}" if query else f"{base}{path}"
        return await self.request("GET", lambda: SignedRequest(url=url, headers={}), pool, weight)
