import time

from exchanges.gateway import ExchangeGateway
from shared.worker import PeriodicWorker

_QUOTE = "USDT"
_STABLE_BASES = frozenset({"USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDP", "USD1", "EUR", "GBP", "AEUR"})
_LEVERAGED = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")

class MarketTickerWorker(PeriodicWorker):
    _TICK_SECONDS = 20
    _LABEL = "MarketTickerWorker"
    _RANK_SECONDS = 24 * 3600
    _TOP_N = 20

    def __init__(self, gateway: ExchangeGateway):
        super().__init__()
        self._gateway = gateway
        self._tickers: list[dict] = []
        self._symbols: list[str] = []
        self._ranked_at = 0.0

    @property
    def tickers(self) -> list[dict]:
        return self._tickers

    async def _tick(self) -> None:
        now = time.monotonic()
        if not self._symbols or now - self._ranked_at >= self._RANK_SECONDS:
            ranked = self._rank(await self._gateway.fetch_binance_tickers())
            if ranked:
                self._symbols = [t["symbol"] for t in ranked]
                self._tickers = ranked
                self._ranked_at = now
            return

        prices = self._prices(await self._gateway.fetch_binance_tickers(self._symbols))
        if prices:
            self._tickers = prices

    def _rank(self, rows: list) -> list[dict]:
        picks = []
        for row in rows:
            symbol = row.get("symbol") or ""
            if not symbol.endswith(_QUOTE) or len(symbol) <= len(_QUOTE):
                continue
            if any(symbol.endswith(suffix) for suffix in _LEVERAGED):
                continue
            if symbol[: -len(_QUOTE)] in _STABLE_BASES:
                continue
            row = self._row(symbol, row)
            if row is not None:
                picks.append(row)

        picks.sort(key=lambda p: p[0], reverse=True)
        return [{"symbol": symbol, "price": price, "change_pct": change} for _, symbol, price, change in picks[: self._TOP_N]]

    def _prices(self, rows: list) -> list[dict]:
        fresh = {}
        for row in rows:
            parsed = self._row(row.get("symbol") or "", row)
            if parsed is not None:
                fresh[parsed[1]] = {"symbol": parsed[1], "price": parsed[2], "change_pct": parsed[3]}
        return [fresh[symbol] for symbol in self._symbols if symbol in fresh]

    @staticmethod
    def _row(symbol: str, row: dict):
        try:
            volume = float(row.get("quoteVolume") or 0)
            price = float(row.get("lastPrice") or 0)
            change = float(row.get("priceChangePercent") or 0)
        except (TypeError, ValueError):
            return None
        if price <= 0:
            return None
        return volume, symbol, price, change
