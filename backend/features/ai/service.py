from datetime import datetime, timedelta, timezone
from time import monotonic

import aiohttp
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.event import EventRepository
from db.repositories.user import UserRepository
from db.session import SessionFactory
from domain.config import Config
from domain.filters import AnalyticsFilters
from domain.models import User
from domain.plans import get_plan
from features.ai.nvidia import complete, stream_complete
from features.ai.prompt import build_user_message, load_skill
from features.ai.schemas import AiInsightBody, AiInsightOut
from features.ai.validation import validate_insight
from features.analytics.cache import AnalyticsCache
from features.analytics.schemas import AnalyticsOut
from features.analytics.service import AnalyticsService
from shared.exceptions import AiUnavailableError, BadRequestError, TooManyRequestsError
from utils.logger import brief, logger

def _as_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def _stored_body(user: User) -> AiInsightBody | None:
    if not user.last_ai_insight:
        return None
    try:
        return AiInsightBody.model_validate_json(user.last_ai_insight)
    except ValidationError:
        return None

def _parse_insight(raw: str) -> AiInsightBody:
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise AiUnavailableError("The AI returned an unreadable response — try again")
    try:
        return AiInsightBody.model_validate_json(raw[start:end + 1])
    except ValidationError:
        raise AiUnavailableError("The AI returned an unexpected format — try again")

class AiService:
    def __init__(self, session: AsyncSession, http: aiohttp.ClientSession, analytics_cache: AnalyticsCache, config: Config):
        self.session = session
        self.http = http
        self.analytics_cache = analytics_cache
        self.config = config
        self._claim_at: datetime | None = None
        self._claim_prev: datetime | None = None

    def state(self, user: User) -> AiInsightOut:
        return self._out(user)

    async def generate(self, user: User) -> AiInsightOut:
        analytics = await self.prepare(user)
        started = monotonic()
        try:
            raw = await complete(
                self.http, self.config.nvidia_base_url, self.config.nvidia_api_key, self.config.nvidia_model,
                load_skill(), build_user_message(analytics)
            )
            body = _parse_insight(raw)
            await self._store(self.session, user, body, analytics, int((monotonic() - started) * 1000))
            self._claim_at = None
            return self._out(user)
        finally:
            await self._release(self.session, user)

    async def stream(self, user: User, analytics: AnalyticsOut):
        started = monotonic()
        parts: list[str] = []
        try:
            async for delta in stream_complete(
                self.http, self.config.nvidia_base_url, self.config.nvidia_api_key, self.config.nvidia_model,
                load_skill(), build_user_message(analytics)
            ):
                parts.append(delta)
                yield "token", delta

            body = _parse_insight("".join(parts))
            async with SessionFactory() as session:
                fresh = await UserRepository(session).get_by_id(user.id)
                target = fresh if fresh is not None else user
                await self._store(session, target, body, analytics, int((monotonic() - started) * 1000))
                self._claim_at = None
                yield "done", self._out(target)
        finally:
            if self._claim_at is not None:
                async with SessionFactory() as session:
                    await self._release(session, user)

    async def prepare(self, user: User) -> AnalyticsOut:
        if not self.config.nvidia_api_key:
            raise AiUnavailableError("AI insights are not configured")
        now = datetime.now(timezone.utc)
        ready_at = self._ready_at(user)
        if ready_at is not None and now < ready_at:
            raise TooManyRequestsError(f"Your next AI insight unlocks {ready_at.isoformat()}")
        analytics = await AnalyticsService(self.session, self.analytics_cache).get_overview(user.id, AnalyticsFilters())
        if analytics.kpis.total_positions == 0:
            raise BadRequestError("Not enough closed positions to analyse yet — sync a few trades first")
        await self._claim(user, now)
        return analytics

    async def _claim(self, user: User, now: datetime) -> None:
        cutoff = now - timedelta(hours=get_plan(user.plan).ai_insight_cooldown_hours)
        prev = _as_utc(user.last_ai_insight_at) if user.last_ai_insight_at is not None else None
        if not await UserRepository(self.session).claim_ai_slot(user.id, now, cutoff):
            unlock = self._ready_at(user)
            raise TooManyRequestsError(
                f"Your next AI insight unlocks {unlock.isoformat()}" if unlock is not None
                else "An insight is already being generated"
            )
        self._claim_at = now
        self._claim_prev = prev

    async def _release(self, session: AsyncSession, user: User) -> None:
        if self._claim_at is None:
            return
        self._claim_at = None
        try:
            await UserRepository(session).reset_ai_slot(user.id, self._claim_prev)
        except Exception as e:
            logger.warning(f"[AiService] failed to release cooldown slot for {user.id}: {brief(e)}")

    async def _store(self, session: AsyncSession, user: User, body: AiInsightBody,
                     analytics: AnalyticsOut, latency_ms: int) -> None:
        validation = validate_insight(body, analytics)
        await UserRepository(session).set_ai_insight(
            user, body.model_dump_json(), datetime.now(timezone.utc), validation["verified"]
        )
        await EventRepository(session).record("ai_insight", user.id, {
            "verdict": body.verdict,
            "verdict_match": validation["verdict_match"],
            "grounding_score": validation["grounding_score"],
            "hallucinated": validation["hallucinated"],
            "net_pnl": analytics.kpis.net_pnl,
            "positions": analytics.kpis.total_positions,
            "model": self.config.nvidia_model,
            "latency_ms": latency_ms
        })

    async def feedback(self, user: User, helpful: bool) -> AiInsightOut:
        if user.last_ai_insight is None:
            raise BadRequestError("No insight to rate yet")
        first = user.last_ai_feedback is None
        await UserRepository(self.session).set_ai_feedback(user, helpful)
        if first:
            await EventRepository(self.session).record("ai_feedback", user.id, {"helpful": helpful})
        return self._out(user)

    @staticmethod
    def _ready_at(user: User) -> datetime | None:
        if user.last_ai_insight_at is None:
            return None
        return _as_utc(user.last_ai_insight_at) + timedelta(hours=get_plan(user.plan).ai_insight_cooldown_hours)

    def _out(self, user: User) -> AiInsightOut:
        ready_at = self._ready_at(user)
        can_generate = ready_at is None or datetime.now(timezone.utc) >= ready_at
        return AiInsightOut(
            insight=_stored_body(user),
            generated_at=_as_utc(user.last_ai_insight_at) if user.last_ai_insight_at is not None else None,
            next_available_at=None if can_generate else ready_at,
            can_generate=can_generate,
            cooldown_hours=get_plan(user.plan).ai_insight_cooldown_hours,
            verified=user.last_ai_verified,
            feedback=user.last_ai_feedback
        )
