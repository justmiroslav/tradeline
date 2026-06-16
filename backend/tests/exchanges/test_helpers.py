from decimal import Decimal

from domain.enums import TradeSide
from exchanges.helpers import abs_or_none, build_url, sign_b64, to_side

class TestBuildUrl:
    def test_with_query(self):
        assert build_url("https://api.x.com", "/v1/a", "k=1&b=2") == "https://api.x.com/v1/a?k=1&b=2"

    def test_without_query(self):
        assert build_url("https://api.x.com", "/v1/a") == "https://api.x.com/v1/a"
        assert build_url("https://api.x.com", "/v1/a", "") == "https://api.x.com/v1/a"

class TestSignB64:
    def test_deterministic_value(self):
        assert sign_b64("secret", "message") == "i19IcCmVwVmMVz2x4hhmqbgl1KeU0WnXBgoDYFeWNgs="

class TestToSide:
    def test_buy_lowercase(self):
        assert to_side("buy") == TradeSide.BUY

    def test_buy_uppercase(self):
        assert to_side("BUY") == TradeSide.BUY

    def test_sell(self):
        assert to_side("sell") == TradeSide.SELL

    def test_anything_else_is_sell(self):
        assert to_side("Sell") == TradeSide.SELL
        assert to_side("anything") == TradeSide.SELL

class TestAbsOrNone:
    def test_none(self):
        assert abs_or_none(None) is None

    def test_negative(self):
        assert abs_or_none(Decimal("-5")) == Decimal("5")

    def test_positive(self):
        assert abs_or_none(Decimal("5")) == Decimal("5")
