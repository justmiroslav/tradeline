import time

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from utils.logger import logger

DEFAULT_RULES = {
    ("POST", "/auth/login"): (10, 60),
    ("POST", "/auth/register"): (5, 60),
    ("POST", "/auth/register/verify"): (3, 600),
    ("POST", "/auth/register/resend"): (3, 60),
    ("POST", "/auth/refresh"): (30, 60),
    ("POST", "/api-keys"): (10, 60)
}

class RateLimiter:
    _MAX_ENTRIES = 10_000

    def __init__(self, rules: dict[tuple[str, str], tuple[int, int]]):
        self._rules = {(method, path.rstrip("/")): rule for (method, path), rule in rules.items()}
        self._counters: dict[tuple[str, str, str], tuple[float, int]] = {}

    def allow(self, method: str, path: str, client_ip: str, now: float | None = None) -> bool:
        route = (method, path.rstrip("/"))
        rule = self._rules.get(route)
        if rule is None:
            return True

        limit, window = rule
        now = time.monotonic() if now is None else now
        key = (client_ip, *route)

        window_start, count = self._counters.get(key, (now, 0))
        if now - window_start >= window:
            window_start, count = now, 0
        if count >= limit:
            self._counters[key] = (window_start, count)
            return False

        self._prune(now)
        self._counters[key] = (window_start, count + 1)
        return True

    def _prune(self, now: float) -> None:
        if len(self._counters) < self._MAX_ENTRIES:
            return
        longest = max(window for _, window in self._rules.values())
        self._counters = {k: v for k, v in self._counters.items() if now - v[0] < longest}

class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, limiter: RateLimiter):
        self._app = app
        self._limiter = limiter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        client_ip = self._client_ip(scope)
        if not self._limiter.allow(scope["method"], scope["path"], client_ip):
            logger.warning(f"[rate-limit] {client_ip} throttled on {scope['method']} {scope['path']}")
            response = JSONResponse(
                status_code=429,
                content={"error": "TooManyRequestsError", "detail": "Too many requests — slow down and retry shortly"}
            )
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)

    @staticmethod
    def _client_ip(scope: Scope) -> str:
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        forwarded = headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[-1].strip()
        client = scope.get("client")
        return client[0] if client else "unknown"
