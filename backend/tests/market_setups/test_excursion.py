from decimal import Decimal as D
from types import SimpleNamespace

from domain.enums import PositionSide
from features.market_setups.worker import _excursion

def _pos(entry, side):
    return SimpleNamespace(entry_price=D(entry), side=side)

def _kl(high, low):
    return SimpleNamespace(high=D(high), low=D(low))

class TestExcursion:
    def test_long_mfe_is_upside_mae_is_downside(self):
        mfe, mae = _excursion(_pos(100, PositionSide.LONG), [_kl(130, 95), _kl(120, 90)])
        assert mfe == D("0.3")
        assert mae == D("0.1")

    def test_short_swaps_favourable_and_adverse(self):
        mfe, mae = _excursion(_pos(100, PositionSide.SHORT), [_kl(130, 95), _kl(120, 90)])
        assert mfe == D("0.1")
        assert mae == D("0.3")

    def test_excursions_never_go_negative(self):
        mfe, mae = _excursion(_pos(100, PositionSide.LONG), [_kl(95, 90)])
        assert mfe == D(0)
        assert mae == D("0.1")

    def test_no_klines_returns_none(self):
        assert _excursion(_pos(100, PositionSide.LONG), []) == (None, None)

    def test_nonpositive_entry_returns_none(self):
        assert _excursion(_pos(0, PositionSide.LONG), [_kl(10, 1)]) == (None, None)
