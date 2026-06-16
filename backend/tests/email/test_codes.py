import re

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from features.email.service import (
    MAX_ATTEMPTS, MAX_SENDS_PER_HOUR, confirm_verification, flush_deliveries, generate_code, hash_code, request_verification
)
from shared.exceptions import InvalidCodeError, TooManyRequestsError
from tests.fakes import FakeCodeRepository as _FakeCodes, FakeEmailSender as _FakeSender

class _FakeUsers:
    @staticmethod
    async def set_email_verified(user):
        user.email_verified = True

class _FailingSender:
    @staticmethod
    async def send(to, subject, text, html):
        raise RuntimeError("provider down")

def _user(verified=False):
    return SimpleNamespace(id=uuid4(), email="trader@example.com", email_verified=verified)

def _sent_code(sender):
    match = re.search(r"\d{6}", sender.sent[-1][2])
    assert match is not None
    return match.group()

class TestCodeGeneration:
    def test_always_six_digits(self):
        for _ in range(50):
            code = generate_code()
            assert len(code) == 6 and code.isdigit()

    def test_hash_is_deterministic_and_opaque(self):
        assert hash_code("123456") == hash_code("123456")
        assert hash_code("123456") != "123456"
        assert len(hash_code("123456")) == 64

class TestRequestCode:
    async def test_sends_code_and_stores_only_the_hash(self):
        codes, sender, user = _FakeCodes(), _FakeSender(), _user()
        await request_verification(codes, sender, user)
        await flush_deliveries()
        assert len(sender.sent) == 1
        assert sender.sent[0][0] == user.email
        code = _sent_code(sender)
        assert codes.codes[0].code_hash == hash_code(code)
        assert code not in codes.codes[0].code_hash

    async def test_resend_within_cooldown_is_blocked(self):
        codes, sender, user = _FakeCodes(), _FakeSender(), _user()
        await request_verification(codes, sender, user)
        with pytest.raises(TooManyRequestsError):
            await request_verification(codes, sender, user)

    async def test_hourly_send_limit(self):
        codes, sender, user = _FakeCodes(), _FakeSender(), _user()
        old = datetime.now(timezone.utc) - timedelta(minutes=30)
        for _ in range(MAX_SENDS_PER_HOUR):
            codes.codes.append(SimpleNamespace(
                user_id=user.id, purpose="verify_email", code_hash="x",
                expires_at=old, attempts=0, consumed_at=old, created_at=old
            ))
        with pytest.raises(TooManyRequestsError):
            await request_verification(codes, sender, user)

    async def test_already_verified_is_rejected(self):
        codes, sender = _FakeCodes(), _FakeSender()
        with pytest.raises(InvalidCodeError):
            await request_verification(codes, sender, _user(verified=True))

    async def test_delivery_failure_does_not_block_the_request(self):
        codes, user = _FakeCodes(), _user()
        await request_verification(codes, _FailingSender(), user)
        await flush_deliveries()
        assert len(codes.codes) == 1
        assert codes.codes[0].consumed_at is None

    async def test_new_code_invalidates_the_previous_one(self):
        codes, sender, users, user = _FakeCodes(), _FakeSender(), _FakeUsers(), _user()
        await request_verification(codes, sender, user)
        await flush_deliveries()
        first_code = _sent_code(sender)
        codes.codes[0].created_at -= timedelta(minutes=2)
        await request_verification(codes, sender, user)
        await flush_deliveries()
        with pytest.raises(InvalidCodeError):
            await confirm_verification(codes, users, user, first_code)

class TestVerifyCode:
    async def test_correct_code_verifies_then_cannot_be_reused(self):
        codes, sender, users, user = _FakeCodes(), _FakeSender(), _FakeUsers(), _user()
        await request_verification(codes, sender, user)
        await flush_deliveries()
        code = _sent_code(sender)
        await confirm_verification(codes, users, user, code)
        assert user.email_verified is True
        assert codes.codes[0].consumed_at is not None
        with pytest.raises(InvalidCodeError):
            await confirm_verification(codes, users, user, code)

    async def test_wrong_code_counts_an_attempt(self):
        codes, sender, users, user = _FakeCodes(), _FakeSender(), _FakeUsers(), _user()
        await request_verification(codes, sender, user)
        await flush_deliveries()
        wrong = "000000" if _sent_code(sender) != "000000" else "111111"
        with pytest.raises(InvalidCodeError):
            await confirm_verification(codes, users, user, wrong)
        assert codes.codes[0].attempts == 1
        assert user.email_verified is False

    async def test_expired_code_is_rejected(self):
        codes, sender, users, user = _FakeCodes(), _FakeSender(), _FakeUsers(), _user()
        await request_verification(codes, sender, user)
        await flush_deliveries()
        code = _sent_code(sender)
        codes.codes[0].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        with pytest.raises(InvalidCodeError):
            await confirm_verification(codes, users, user, code)

    async def test_exhausted_attempts_block_even_the_correct_code(self):
        codes, sender, users, user = _FakeCodes(), _FakeSender(), _FakeUsers(), _user()
        await request_verification(codes, sender, user)
        await flush_deliveries()
        code = _sent_code(sender)
        codes.codes[0].attempts = MAX_ATTEMPTS
        with pytest.raises(InvalidCodeError):
            await confirm_verification(codes, users, user, code)
        assert user.email_verified is False
