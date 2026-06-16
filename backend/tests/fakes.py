from datetime import datetime, timezone
from types import SimpleNamespace

class FakeCodeRepository:
    def __init__(self):
        self.codes = []

    async def create(self, user_id, purpose, code_hash, expires_at):
        now = datetime.now(timezone.utc)
        for c in self._owned(user_id, purpose):
            if c.consumed_at is None:
                c.consumed_at = now
        code = SimpleNamespace(
            user_id=user_id, purpose=purpose, code_hash=code_hash,
            expires_at=expires_at, attempts=0, consumed_at=None, created_at=now
        )
        self.codes.append(code)
        return code

    async def latest_active(self, user_id, purpose):
        now = datetime.now(timezone.utc)
        active = [c for c in self._owned(user_id, purpose) if c.consumed_at is None and c.expires_at > now]
        return active[-1] if active else None

    async def count_recent(self, user_id, purpose, since):
        return len([c for c in self._owned(user_id, purpose) if c.created_at >= since])

    @staticmethod
    async def record_attempt(code):
        code.attempts += 1

    @staticmethod
    async def consume(code):
        code.consumed_at = datetime.now(timezone.utc)

    def _owned(self, user_id, purpose):
        return [c for c in self.codes if c.user_id == user_id and c.purpose == purpose]

class FakeEmailSender:
    def __init__(self):
        self.sent = []

    async def send(self, to, subject, text, html):
        self.sent.append((to, subject, text, html))
