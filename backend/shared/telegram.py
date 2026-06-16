import aiohttp

from typing import Optional

from utils.logger import brief, logger

class TelegramClient:
    _BASE = "https://api.telegram.org"

    def __init__(self, http: aiohttp.ClientSession, token: str, chat_id: str, review_chat_id: str = ""):
        self._http = http
        self._token = token
        self.chat_id = chat_id
        self.review_chat_id = review_chat_id or chat_id

    async def notify_review(self, text: str) -> None:
        await self.send(self.review_chat_id, text, parse_mode="HTML")

    async def _post(self, method: str, body: dict, *, label: str, warn: bool = True) -> Optional[dict]:
        try:
            async with self._http.post(f"{self._BASE}/bot{self._token}/{method}", json=body) as resp:
                if resp.status != 200:
                    (logger.warning if warn else logger.debug)(f"[telegram] {method} {resp.status}: {(await resp.text())[:200]}")
                    return None
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            logger.warning(f"[telegram] {label} failed: {brief(e)}")
            return None

    async def send(self, chat_id: str, text: str, *, reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> Optional[int]:
        body = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        if reply_markup is not None:
            body["reply_markup"] = reply_markup
        if parse_mode is not None:
            body["parse_mode"] = parse_mode
        data = await self._post("sendMessage", body, label="send")
        return data["result"]["message_id"] if data is not None else None

    async def edit_message(self, chat_id: str, message_id: int, text: str, *, reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> None:
        body = {"chat_id": chat_id, "message_id": message_id, "text": text, "disable_web_page_preview": True}
        if reply_markup is not None:
            body["reply_markup"] = reply_markup
        if parse_mode is not None:
            body["parse_mode"] = parse_mode
        await self._post("editMessageText", body, label="edit", warn=False)

    async def answer_callback(self, callback_query_id: str, text: str = "") -> None:
        body = {"callback_query_id": callback_query_id}
        if text:
            body["text"] = text
        await self._post("answerCallbackQuery", body, label="answer")

    async def get_updates(self, offset: int, timeout: int = 20) -> list[dict]:
        async with self._http.post(
            f"{self._BASE}/bot{self._token}/getUpdates",
            json={"offset": offset, "timeout": timeout},
            timeout=aiohttp.ClientTimeout(total=timeout + 15)
        ) as resp:
            data = await resp.json()
        return data.get("result", []) if data.get("ok") else []
