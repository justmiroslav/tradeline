import html
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.repositories.review import ReviewRepository
from features.metrics.service import MetricsService
from shared.telegram import TelegramClient
from shared.worker import PeriodicWorker

def _kb(rows: list[list[tuple[str, str]]]) -> dict:
    return {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in rows]}

_BACK = _kb([[("⬅ Back", "menu")]])

class TelegramBot(PeriodicWorker):
    _TICK_SECONDS = 1
    _LABEL = "TelegramBot"

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], client: TelegramClient):
        super().__init__()
        self._sf = session_factory
        self._client = client
        self._offset = 0

    async def _tick(self) -> None:
        updates = await self._client.get_updates(self._offset, timeout=20)
        for update in updates:
            self._offset = update["update_id"] + 1
            if "callback_query" in update:
                await self._on_callback(update["callback_query"])
            elif "message" in update:
                await self._on_message(update["message"])

    async def _on_message(self, message: dict) -> None:
        sender = str((message.get("from") or {}).get("id") or "")
        chat_id = str((message.get("chat") or {}).get("id") or "")
        if not chat_id or sender != self._client.chat_id:
            return
        text, kb = await self._main_menu()
        await self._client.send(chat_id, text, reply_markup=kb, parse_mode="HTML")

    async def _on_callback(self, cq: dict) -> None:
        sender = str((cq.get("from") or {}).get("id") or "")
        if sender != self._client.chat_id:
            return
        cq_id = cq["id"]
        data = cq.get("data") or ""
        message = cq.get("message") or {}
        chat_id = str((message.get("chat") or {}).get("id") or "")
        message_id = message.get("message_id")
        if not chat_id or message_id is None:
            await self._client.answer_callback(cq_id)
            return

        async with self._sf() as session:
            if data == "menu":
                text, kb = await self._main_menu()
            elif data == "metrics":
                text, kb = await self._metrics_view(session)
            elif data.startswith("m:"):
                text, kb = await self._metric_detail(session, data.split(":", 1)[1])
            elif data == "reviews":
                text, kb = await self._reviews_view(session)
            elif data == "approved":
                text, kb = await self._approved_view(session)
            elif data.startswith("approve:") or data.startswith("reject:"):
                action, _, raw_id = data.partition(":")
                toast = await self._moderate(session, raw_id, "approved" if action == "approve" else "rejected")
                await self._client.answer_callback(cq_id, toast)
                text, kb = await self._reviews_view(session)
                await self._client.edit_message(chat_id, message_id, text, reply_markup=kb, parse_mode="HTML")
                return
            else:
                await self._client.answer_callback(cq_id)
                return

        await self._client.answer_callback(cq_id)
        await self._client.edit_message(chat_id, message_id, text, reply_markup=kb, parse_mode="HTML")

    async def _main_menu(self) -> tuple[str, dict]:
        text = "<b>Tradeline control</b>\nPick a section"
        kb = _kb([
            [("\U0001F4CA Metrics", "metrics")],
            [("⭐ Pending reviews", "reviews"), ("✓ Approved", "approved")],
        ])
        return text, kb

    async def _metrics_view(self, session: AsyncSession) -> tuple[str, dict]:
        text = await MetricsService(session).overview()
        kb = _kb([
            [("\U0001F4C8 Activation", "m:funnel"), ("\U0001F916 AI quality", "m:ai")],
            [("⭐ Satisfaction", "m:sat"), ("\U0001F4CB Raw events", "m:raw")],
            [("⬅ Back", "menu")],
        ])
        return text, kb

    async def _metric_detail(self, session: AsyncSession, key: str) -> tuple[str, dict]:
        service = MetricsService(session)
        renderers = {
            "funnel": service.funnel,
            "ai": service.ai_correctness,
            "sat": service.satisfaction,
            "raw": service.raw_events,
        }
        render = renderers.get(key)
        if render is None:
            return await self._metrics_view(session)
        return await render(), _kb([[("⬅ Metrics", "metrics")]])

    async def _reviews_view(self, session: AsyncSession) -> tuple[str, dict]:
        rows = await ReviewRepository(session).by_status("pending")
        if not rows:
            return "<b>Pending reviews</b>\n\nNothing waiting — all caught up", _BACK
        review = rows[-1]
        name = html.escape(review.user.name) if review.user else "—"
        body = html.escape(review.body or "")
        date = review.created_at.strftime("%Y-%m-%d") if review.created_at else ""
        text = (
            f"<b>Pending review</b> (1 of {len(rows)})\n"
            f"{date}\n\n"
            f"{review.rating}★ — <b>{name}</b>\n{body}"
        )
        kb = _kb([
            [("✅ Approve", f"approve:{review.id}"), ("❌ Reject", f"reject:{review.id}")],
            [("⬅ Back", "menu")],
        ])
        return text, kb

    async def _approved_view(self, session: AsyncSession) -> tuple[str, dict]:
        rows = await ReviewRepository(session).by_status("approved")
        if not rows:
            return "<b>Approved reviews</b>\n\nNone yet", _BACK
        blocks = []
        for r in rows:
            name = html.escape(r.user.name) if r.user else "—"
            blocks.append(f"{r.rating}★ {name} — {html.escape(r.body or '')}")
        return "<b>Approved reviews</b>\n\n" + "\n\n".join(blocks), _BACK

    @staticmethod
    async def _moderate(session: AsyncSession, raw_id: str, status: str) -> str:
        try:
            review_id = uuid.UUID(raw_id)
        except ValueError:
            return "Gone"
        repo = ReviewRepository(session)
        review = await repo.get(review_id)
        if review is None:
            return "Gone"
        await repo.set_status(review, status)
        return "✅ Approved" if status == "approved" else "❌ Rejected"
