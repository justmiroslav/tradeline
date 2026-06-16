from domain.enums import Exchange, MarketType

from .config import ENDPOINTS
from .http_executor import RequestExecutor

async def fetch_binance_symbols(market_type: MarketType, executor: RequestExecutor) -> list:
    ep = ENDPOINTS[Exchange.BINANCE]
    if market_type == MarketType.SPOT:
        data = await executor.get_public(ep.url, "/api/v3/exchangeInfo", "spot", weight=20)
        is_futures = False
    else:
        data = await executor.get_public(ep.futures_url, "/fapi/v1/exchangeInfo", "fut", weight=1)
        is_futures = True

    out = []
    for s in data.get("symbols", []):
        if s.get("quoteAsset") != "USDT" or s.get("status") != "TRADING":
            continue
        if is_futures and s.get("contractType") != "PERPETUAL":
            continue
        out.append(s["symbol"])
    return out

PUBLIC_SYMBOL_FETCHERS = {
    Exchange.BINANCE: fetch_binance_symbols
}
