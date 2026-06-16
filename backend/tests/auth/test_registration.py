import re

from types import SimpleNamespace
from uuid import uuid4

import pytest

from features.auth.service import complete_registration, resend_registration_code, start_registration
from features.email.service import flush_deliveries
from shared.exceptions import ConflictError, UnauthorizedError
from shared.security import verify_password
from tests.fakes import FakeCodeRepository, FakeEmailSender

class _FakeSession:
    def add(self, obj):
        pass

    async def commit(self):
        pass

class _FakeUsers:
    def __init__(self):
        self.users = []
        self.session = _FakeSession()

    async def get_by_email(self, email):
        return next((u for u in self.users if u.email == email), None)

    async def create(self, email, name, password_hash):
        user = SimpleNamespace(id=uuid4(), email=email, name=name, password_hash=password_hash, email_verified=False)
        self.users.append(user)
        return user

    @staticmethod
    async def replace_unverified(user, name, password_hash):
        user.name = name
        user.password_hash = password_hash
        return user

    @staticmethod
    async def set_email_verified(user):
        user.email_verified = True

def _sent_code(sender: FakeEmailSender) -> str:
    match = re.search(r"\d{6}", sender.sent[-1][2])
    assert match is not None
    return match.group()

class TestRegistrationFlow:
    async def test_account_is_usable_only_after_code_verification(self):
        users, codes, sender = _FakeUsers(), FakeCodeRepository(), FakeEmailSender()

        await start_registration(users, codes, sender, email="new@trader.dev", name="Trader", password="secret123")
        await flush_deliveries()
        created = users.users[0]
        assert created.email_verified is False
        assert len(sender.sent) == 1

        user = await complete_registration(users, codes, email="new@trader.dev", code=_sent_code(sender))
        assert user is created
        assert user.email_verified is True

    async def test_verified_email_cannot_register_again(self):
        users, codes, sender = _FakeUsers(), FakeCodeRepository(), FakeEmailSender()
        verified = SimpleNamespace(id=uuid4(), email="taken@trader.dev", name="Old", password_hash="x", email_verified=True)
        users.users.append(verified)

        with pytest.raises(ConflictError):
            await start_registration(users, codes, sender, email="taken@trader.dev", name="New", password="secret123")

    async def test_unverified_registration_is_replaced_not_rejected(self):
        users, codes, sender = _FakeUsers(), FakeCodeRepository(), FakeEmailSender()
        await start_registration(users, codes, sender, email="redo@trader.dev", name="First", password="firstpass1")
        await flush_deliveries()
        codes.codes[0].created_at = codes.codes[0].created_at.replace(year=2000)

        await start_registration(users, codes, sender, email="redo@trader.dev", name="Second", password="secondpass2")
        await flush_deliveries()

        assert len(users.users) == 1
        assert users.users[0].name == "Second"
        assert verify_password("secondpass2", users.users[0].password_hash)
        user = await complete_registration(users, codes, email="redo@trader.dev", code=_sent_code(sender))
        assert user.email_verified is True

    async def test_verify_without_pending_registration_is_rejected(self):
        users, codes = _FakeUsers(), FakeCodeRepository()

        with pytest.raises(UnauthorizedError):
            await complete_registration(users, codes, email="ghost@trader.dev", code="123456")

    async def test_resend_requires_a_pending_registration(self):
        users, codes, sender = _FakeUsers(), FakeCodeRepository(), FakeEmailSender()
        verified = SimpleNamespace(id=uuid4(), email="done@trader.dev", name="Done", password_hash="x", email_verified=True)
        users.users.append(verified)

        with pytest.raises(UnauthorizedError):
            await resend_registration_code(users, codes, sender, email="done@trader.dev")
        with pytest.raises(UnauthorizedError):
            await resend_registration_code(users, codes, sender, email="ghost@trader.dev")
