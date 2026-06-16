import jwt
from freezegun import freeze_time

from domain.config import get_config
from shared.security import (
    create_access_token, create_refresh_token, decode_token, encrypt, decrypt,
    hash_api_key, hash_password, verify_password
)

class TestJwt:
    _UID = "00000000-0000-4000-8000-000000000001"
    _FAM = "00000000-0000-4000-8000-0000000000fa"
    _JTI = "00000000-0000-4000-8000-0000000000c1"

    def test_roundtrip(self):
        token = create_access_token(self._UID, token_version=1)
        assert decode_token(token) == (self._UID, 1)

    def test_garbage_token_returns_none(self):
        assert decode_token("not-a-jwt") is None

    def test_expired_token_returns_none(self):
        with freeze_time("2026-01-01 00:00:00"):
            token = create_access_token("u", token_version=1)
        with freeze_time("2026-01-03 00:00:00"):
            assert decode_token(token) is None

    def test_wrong_secret_returns_none(self):
        bad = jwt.encode({"sub": "u", "ver": 1}, "completely-different-secret-32-bytes-long", algorithm="HS256")
        assert decode_token(bad) is None

    def test_missing_version_field_returns_none(self):
        token = jwt.encode({"sub": self._UID, "typ": "access"}, get_config().jwt_secret, algorithm="HS256")
        assert decode_token(token) is None

    def test_token_carries_version(self):
        token = create_access_token(self._UID, token_version=42)
        assert decode_token(token) == (self._UID, 42)

    def test_non_uuid_subject_returns_none(self):
        token = create_access_token("user-123", token_version=1)
        assert decode_token(token) is None

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token(self._UID, token_version=3, family_id=self._FAM, jti=self._JTI)
        assert decode_token(token, expected_type="refresh") == (self._UID, 3)

    def test_refresh_token_rejected_as_access_token(self):
        token = create_refresh_token(self._UID, token_version=1, family_id=self._FAM, jti=self._JTI)
        assert decode_token(token) is None

    def test_access_token_rejected_as_refresh_token(self):
        token = create_access_token(self._UID, token_version=1)
        assert decode_token(token, expected_type="refresh") is None

class TestFernet:
    def test_roundtrip(self):
        cipher = encrypt("hello world")
        assert cipher != "hello world"
        assert decrypt(cipher) == "hello world"

    def test_unicode_roundtrip(self):
        s = "пароль🔑 with emoji"
        assert decrypt(encrypt(s)) == s

    def test_two_encryptions_differ_due_to_iv(self):
        a = encrypt("same")
        b = encrypt("same")
        assert a != b
        assert decrypt(a) == decrypt(b) == "same"

class TestHashApiKey:
    def test_deterministic(self):
        h1 = hash_api_key("apikey-abc123")
        h2 = hash_api_key("apikey-abc123")
        assert h1 == h2
        assert len(h1) == 64

    def test_different_keys_different_hashes(self):
        assert hash_api_key("a") != hash_api_key("b")

class TestPassword:
    def test_hash_and_verify(self):
        h = hash_password("hunter2")
        assert h != "hunter2"
        assert verify_password("hunter2", h)
        assert not verify_password("wrong", h)

    def test_two_hashes_differ_due_to_salt(self):
        a = hash_password("x")
        b = hash_password("x")
        assert a != b
        assert verify_password("x", a) and verify_password("x", b)
