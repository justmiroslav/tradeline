from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from exchanges.binance.rest import BinanceClient
from exchanges.bitget.rest import BitgetClient
from exchanges.bybit.rest import BybitClient
from exchanges.okx.rest import OKXClient
from exchanges.types import DecryptedCredentials
from shared.exceptions import InvalidCredentialsError, KeyAccessRestrictedError, KeyNotReadOnlyError

_NO_EXEC: Any = None

@pytest.fixture
def binance_client():
    return BinanceClient(_NO_EXEC, DecryptedCredentials("k", "s"))

@pytest.fixture
def bybit_client():
    return BybitClient(_NO_EXEC, DecryptedCredentials("k", "s"))

@pytest.fixture
def okx_client():
    return OKXClient(_NO_EXEC, DecryptedCredentials("k", "s", "p"))

@pytest.fixture
def bitget_client():
    return BitgetClient(_NO_EXEC, DecryptedCredentials("k", "s", "p"))

def _path_arg(args: tuple) -> str | None:
    return args[2] if len(args) > 2 else None

class TestBinanceReadOnly:
    async def test_readonly_passes(self, binance_client):
        c = binance_client
        ro = {"enableReading": True, "enableFutures": True}
        async def fake(*args, **_):
            return ro if _path_arg(args) == c._API_RESTRICTIONS else {"balances": []}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.spot is True and caps.futures is True

    async def test_trade_perm_rejected(self, binance_client):
        c = binance_client
        bad = {"enableReading": True, "enableSpotAndMarginTrading": True}
        async def fake(*args, **_):
            return bad if _path_arg(args) == c._API_RESTRICTIONS else {"balances": []}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            with pytest.raises(KeyNotReadOnlyError, match="enableSpotAndMarginTrading"):
                await c.validate_credentials()

class TestBybitReadOnly:
    async def test_readonly_passes(self, bybit_client):
        c = bybit_client
        async def fake(*args, **_):
            return {"readOnly": 1, "permissions": {"Spot": ["SpotTrade"], "ContractTrade": ["Order", "Position"]}} if _path_arg(args) == c._QUERY_API else {"list": []}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.spot and caps.futures

    async def test_non_readonly_rejected(self, bybit_client):
        c = bybit_client
        async def fake(*args, **_):
            return {"readOnly": 0} if _path_arg(args) == c._QUERY_API else {"list": []}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            with pytest.raises(KeyNotReadOnlyError):
                await c.validate_credentials()

class TestOKXReadOnly:
    async def test_readonly_passes(self, okx_client):
        c = okx_client
        with patch.object(c, "_request", new=AsyncMock(return_value={"code": "0", "data": [{"perm": "read_only"}]})):
            caps = await c.validate_credentials()
        assert caps.spot and caps.futures

    async def test_trade_perm_rejected(self, okx_client):
        c = okx_client
        with patch.object(c, "_request", new=AsyncMock(return_value={"code": "0", "data": [{"perm": "read_only,trade"}]})):
            with pytest.raises(KeyNotReadOnlyError, match="trade"):
                await c.validate_credentials()

    async def test_passphrase_required(self):
        c = OKXClient(_NO_EXEC, DecryptedCredentials("k", "s"))
        with pytest.raises(InvalidCredentialsError, match="passphrase"):
            await c.validate_credentials()

class TestIpExtraction:
    async def test_binance_reads_the_iprestrict_flag(self, binance_client):
        c = binance_client
        ro = {"enableReading": True, "ipRestrict": True}
        async def fake(*args, **_):
            return ro if _path_arg(args) == c._API_RESTRICTIONS else {"balances": [], "uid": 7}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.ip_restricted is True

    async def test_bybit_ip_list_means_restricted(self, bybit_client):
        c = bybit_client
        async def fake(*args, **_):
            return {"readOnly": 1, "ips": ["1.2.3.4"], "permissions": {"Spot": ["SpotTrade"]}} if _path_arg(args) == c._QUERY_API else {"list": []}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.ip_restricted is True

    async def test_bybit_wildcard_means_unrestricted(self, bybit_client):
        c = bybit_client
        async def fake(*args, **_):
            return {"readOnly": 1, "ips": ["*"], "permissions": {"ContractTrade": ["Position"]}} if _path_arg(args) == c._QUERY_API else {"list": []}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.ip_restricted is False

    async def test_okx_reads_the_bound_ip_string(self, okx_client):
        c = okx_client
        payload = {"code": "0", "data": [{"perm": "read_only", "ip": "1.2.3.4,5.6.7.8"}]}
        with patch.object(c, "_request", new=AsyncMock(return_value=payload)):
            caps = await c.validate_credentials()
        assert caps.ip_restricted is True

    async def test_bitget_reads_the_bound_ips(self, bitget_client):
        c = bitget_client
        async def fake(*args, **_):
            if _path_arg(args) == c._SPOT_INFO:
                return {"code": "00000", "data": {"authorities": ["coor"], "ips": "1.2.3.4"}}
            return {"code": "00000", "data": [{}]}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.ip_restricted is True

class TestBitgetReadOnly:
    async def test_readonly_passes(self, bitget_client):
        c = bitget_client
        async def fake(*args, **_):
            if _path_arg(args) == c._SPOT_INFO:
                return {"code": "00000", "data": {"authorities": ["coor", "cpor", "stor"]}}
            return {"code": "00000", "data": [{}]}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.spot and caps.futures

    async def test_write_scope_rejected(self, bitget_client):
        c = bitget_client
        async def fake(*args, **_):
            if _path_arg(args) == c._SPOT_INFO:
                return {"code": "00000", "data": {"authorities": ["coor", "stow"]}}
            return {"code": "00000", "data": [{}]}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            with pytest.raises(KeyNotReadOnlyError, match="stow"):
                await c.validate_credentials()

    async def test_empty_authorities_fail_closed(self, bitget_client):
        c = bitget_client
        async def fake(*args, **_):
            if _path_arg(args) == c._SPOT_INFO:
                return {"code": "00000", "data": {"authorities": []}}
            return {"code": "00000", "data": [{}]}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            with pytest.raises(KeyNotReadOnlyError, match="cannot read"):
                await c.validate_credentials()

    async def test_passphrase_required(self):
        c = BitgetClient(_NO_EXEC, DecryptedCredentials("k", "s"))
        with pytest.raises(InvalidCredentialsError, match="passphrase"):
            await c.validate_credentials()

class TestMarketSeparation:
    async def test_bitget_spot_only_key(self, bitget_client):
        c = bitget_client
        async def fake(*args, **_):
            if _path_arg(args) == c._SPOT_INFO:
                return {"code": "00000", "data": {"authorities": ["stor"]}}
            return {"code": "00000", "data": [{}]}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.spot is True and caps.futures is False

    async def test_bitget_futures_only_key(self, bitget_client):
        c = bitget_client
        async def fake(*args, **_):
            if _path_arg(args) == c._SPOT_INFO:
                return {"code": "00000", "data": {"authorities": ["coor", "cpor"]}}
            return {"code": "00000", "data": [{}]}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.spot is False and caps.futures is True

    async def test_bybit_spot_only_key(self, bybit_client):
        c = bybit_client
        async def fake(*args, **_):
            if _path_arg(args) == c._QUERY_API:
                return {"readOnly": 1, "permissions": {"Spot": ["SpotTrade"], "ContractTrade": []}}
            return {"list": []}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.spot is True and caps.futures is False

    async def test_bybit_contract_only_key(self, bybit_client):
        c = bybit_client
        async def fake(*args, **_):
            if _path_arg(args) == c._QUERY_API:
                return {"readOnly": 1, "permissions": {"Spot": [], "ContractTrade": ["Position"]}}
            return {"list": []}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.spot is False and caps.futures is True

    async def test_bitget_no_market_permissions_rejected(self, bitget_client):
        c = bitget_client
        async def fake(*args, **_):
            if _path_arg(args) == c._SPOT_INFO:
                return {"code": "00000", "data": {"authorities": ["wtor"]}}
            return {"code": "00000", "data": [{}]}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            with pytest.raises(KeyAccessRestrictedError):
                await c.validate_credentials()

    async def test_binance_reading_only_key_is_spot_only(self, binance_client):
        c = binance_client
        ro = {"enableReading": True, "enableFutures": False}
        async def fake(*args, **_):
            return ro if _path_arg(args) == c._API_RESTRICTIONS else {"balances": [], "uid": 7}
        with patch.object(c, "_request", new=AsyncMock(side_effect=fake)):
            caps = await c.validate_credentials()
        assert caps.spot is True and caps.futures is False
