import pytest

from domain.config import get_config
from domain.enums import Exchange
from exchanges.types import KeyCapabilities
from features.api_keys.service import ensure_ip_restricted
from shared.exceptions import IpNotRestrictedError

def _caps(restricted: bool) -> KeyCapabilities:
    return KeyCapabilities(spot=True, futures=True, account_uid="1", ip_restricted=restricted)

@pytest.fixture
def enforced(monkeypatch):
    monkeypatch.setenv("PROXY_POOL_CSV", "http://user:pass@10.0.0.5:3128")
    get_config.cache_clear()
    yield get_config()
    get_config.cache_clear()

@pytest.fixture
def disabled(monkeypatch):
    monkeypatch.setenv("PROXY_POOL_CSV", "")
    get_config.cache_clear()
    yield
    get_config.cache_clear()

class TestIpPolicy:
    def test_restricted_key_passes(self, enforced):
        ensure_ip_restricted(_caps(True), Exchange.BYBIT)

    def test_unrestricted_key_is_rejected_naming_exchange_and_ip(self, enforced):
        with pytest.raises(IpNotRestrictedError, match=r"Bybit.*10\.0\.0\.5"):
            ensure_ip_restricted(_caps(False), Exchange.BYBIT)

    def test_policy_disabled_without_a_pool(self, disabled):
        ensure_ip_restricted(_caps(False), Exchange.BYBIT)
