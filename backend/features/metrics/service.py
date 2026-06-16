from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.event import EventRepository
from db.repositories.review import ReviewRepository

def _pct(part: int, whole: int) -> str:
    return f"{(100 * part / whole):.0f}%" if whole else "n/a"

class MetricsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def overview(self) -> str:
        events = EventRepository(self.session)
        reviews = ReviewRepository(self.session)

        funnel = await events.distinct_user_counts()
        insights = await events.by_type("ai_insight")
        pending = await reviews.by_status("pending")
        approved = await reviews.by_status("approved")

        signed = funnel.get("signup", 0)
        n = len(insights)
        verdict_ok = sum(1 for e in insights if e.payload.get("verdict_match"))
        all_reviews = pending + approved
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0

        return (
            "<b>\U0001F4CA Validation matrix</b>\n\n"
            f"{signed} signups | {n} insights generated\n"
            f"verdict accuracy {_pct(verdict_ok, n)} | avg {avg_rating:.1f}★\n\n"
            "Pick a category"
        )

    async def funnel(self) -> str:
        events = EventRepository(self.session)
        funnel = await events.distinct_user_counts()
        signed = funnel.get("signup", 0)

        block = "\n".join([
            f"signed up:        {signed}",
            f"connected a key:  {funnel.get('key_added', 0)}  ({_pct(funnel.get('key_added', 0), signed)})",
            f"got synced data:  {funnel.get('sync_done', 0)}  ({_pct(funnel.get('sync_done', 0), signed)})",
            f"used AI insight:  {funnel.get('ai_insight', 0)}  ({_pct(funnel.get('ai_insight', 0), signed)})",
            f"rated the AI:     {funnel.get('ai_feedback', 0)}  ({_pct(funnel.get('ai_feedback', 0), signed)})",
            f"left a review:    {funnel.get('review_submitted', 0)}  ({_pct(funnel.get('review_submitted', 0), signed)})",
        ])
        return f"<b>Activation funnel</b> (distinct users)\n<pre>{block}</pre>"

    async def ai_correctness(self) -> str:
        events = EventRepository(self.session)
        insights = await events.by_type("ai_insight")

        n = len(insights)
        verdict_ok = sum(1 for e in insights if e.payload.get("verdict_match"))
        grounded = sum(1 for e in insights if not e.payload.get("hallucinated"))
        grounding_avg = sum(float(e.payload.get("grounding_score") or 0) for e in insights) / n if n else 0
        latency_avg = sum(int(e.payload.get("latency_ms") or 0) for e in insights) / n if n else 0

        block = "\n".join([
            f"insights generated: {n}",
            f"verdict accuracy:   {_pct(verdict_ok, n)}  (matched real net PnL)",
            f"grounded:           {_pct(grounded, n)}  (no hallucinated symbols)",
            f"avg grounding: {grounding_avg:.2f} | avg latency: {latency_avg / 1000:.1f}s",
        ])
        return f"<b>AI correctness</b>\n<pre>{block}</pre>"

    async def satisfaction(self) -> str:
        events = EventRepository(self.session)
        reviews = ReviewRepository(self.session)

        feedback = await events.by_type("ai_feedback")
        pending = await reviews.by_status("pending")
        approved = await reviews.by_status("approved")

        helpful = sum(1 for e in feedback if e.payload.get("helpful"))
        all_reviews = pending + approved
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0

        block = "\n".join([
            f"AI helpful: {_pct(helpful, len(feedback))} of {len(feedback)} ratings",
            f"reviews: {len(approved)} approved, {len(pending)} pending | avg {avg_rating:.1f}★",
        ])
        return f"<b>Satisfaction</b>\n<pre>{block}</pre>"

    async def raw_events(self) -> str:
        events = EventRepository(self.session)
        counts = await events.counts()
        block = "\n".join(f"{t}: {c}" for t, c in sorted(counts.items())) or "none"
        return f"<b>Raw events</b> (all time)\n<pre>{block}</pre>"
