from typing import Protocol

import aiohttp

from shared.exceptions import EmailDeliveryError
from utils.logger import logger

class EmailSender(Protocol):
    async def send(self, to: str, subject: str, text: str, html: str) -> None: ...

class LogEmailSender:
    async def send(self, to: str, subject: str, text: str, html: str) -> None:
        logger.info(f"[email] to={to} subject={subject!r} body={text!r}")

class ResendEmailSender:
    _URL = "https://api.resend.com/emails"

    def __init__(self, http: aiohttp.ClientSession, api_key: str, sender: str):
        self._http = http
        self._api_key = api_key
        self._sender = sender

    async def send(self, to: str, subject: str, text: str, html: str) -> None:
        payload = {"from": self._sender, "to": [to], "subject": subject, "text": text, "html": html}
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            async with self._http.post(self._URL, json=payload, headers=headers) as resp:
                if resp.status >= 400:
                    detail = (await resp.text())[:200]
                    logger.warning(f"[email] Resend rejected the message ({resp.status}): {detail}")
                    raise EmailDeliveryError("Could not send the email — try again later")
        except aiohttp.ClientError as e:
            logger.warning(f"[email] Resend unreachable: {e}")
            raise EmailDeliveryError("Could not send the email — try again later")
