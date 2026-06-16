import aiohttp

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.api_key import initial_next_check
from domain.config import get_config
from domain.enums import Exchange, MarketType, PlanTier, TradeSide
from domain.models import ApiKey, MarketUniverse, Trade, User
from shared.security import encrypt, hash_api_key, hash_password
from utils.logger import brief, logger

DEMO_EMAIL = "mirosmale@gmail.com"
DEMO_USER_ID = UUID("00000000-0000-4000-8000-000000000001")

_KLINES_URL = "https://api.binance.com/api/v3/klines"
_HOURS_PER_PAGE = 1000
_OLDEST_DAYS = 62
_FALLBACK_PRICES = {
    "BTCUSDT": "72000", "ETHUSDT": "2200", "SOLUSDT": "85", "BNBUSDT": "650", "XRPUSDT": "1.50",
    "DOGEUSDT": "0.16", "ADAUSDT": "0.45", "AVAXUSDT": "28", "LINKUSDT": "14", "ARBUSDT": "0.65",
    "OPUSDT": "1.45", "DOTUSDT": "4.2", "ATOMUSDT": "5.5", "LTCUSDT": "75", "APTUSDT": "7.5"
}

@dataclass(frozen=True, slots=True)
class PriceBook:
    _closes: dict[str, dict[tuple[int, int], Decimal]]

    def at(self, symbol: str, days_ago: int, hour: int) -> Decimal:
        real = self._closes.get(symbol, {}).get((days_ago, hour))
        if real is not None:
            return real
        wobble = Decimal((days_ago * 7 + hour * 3) % 11 - 5) / 100
        return Decimal(_FALLBACK_PRICES[symbol]) * (1 + wobble)

async def _load_price_book(http: aiohttp.ClientSession) -> PriceBook:
    now = datetime.now(timezone.utc)
    start_ms = int((now - timedelta(days=_OLDEST_DAYS + 1)).timestamp() * 1000)
    closes: dict[str, dict[tuple[int, int], Decimal]] = {}

    try:
        for symbol in _FALLBACK_PRICES:
            rows: list = []
            cursor = start_ms
            while True:
                params = {"symbol": symbol, "interval": "1h", "startTime": str(cursor), "limit": str(_HOURS_PER_PAGE)}
                async with http.get(_KLINES_URL, params=params) as resp:
                    page = await resp.json()
                if not isinstance(page, list) or not page:
                    break
                rows.extend(page)
                if len(page) < _HOURS_PER_PAGE:
                    break
                cursor = page[-1][0] + 3_600_000

            book = {}
            for row in rows:
                opened = datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc)
                book[((now.date() - opened.date()).days, opened.hour)] = Decimal(row[4])
            closes[symbol] = book
    except (aiohttp.ClientError, TimeoutError, ValueError) as e:
        logger.warning(f"[seed] reference prices unavailable ({brief(e)}) — seeding with static price levels")
        return PriceBook({})

    logger.info(f"[seed] loaded real hourly prices for {len(closes)} symbols (Binance public klines)")
    return PriceBook(closes)

def _ts(days_ago: int, hour: int = 12, minute: int = 0) -> datetime:
    moment = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return moment.replace(hour=hour, minute=minute, second=0, microsecond=0)

def _t(uid: UUID, kid: UUID, ex: Exchange, mt: MarketType, sym: str, side: TradeSide,
       price: Decimal, qty: Decimal, when: datetime, tid: str, pnl: Decimal | None = None) -> Trade:
    return Trade(
        user_id=uid, api_key_id=kid, exchange=ex, market_type=mt, symbol=sym, side=side,
        price=price, quantity=qty, fee=price * qty * Decimal("0.001"),
        realized_pnl=pnl, time=when, trade_id=tid
    )

def _spot(book: PriceBook, uid: UUID, kid: UUID, ex: Exchange, sym: str,
          qtys: list[str], open_days: list[int], close_day: int, tag: str) -> list[Trade]:
    rows = []
    total = Decimal(0)
    for i, (qty, day) in enumerate(zip(qtys, open_days)):
        price = book.at(sym, day, 10)
        rows.append(_t(uid, kid, ex, MarketType.SPOT, sym, TradeSide.BUY, price, Decimal(qty), _ts(day, 10), f"{tag}-b{i}"))
        total += Decimal(qty)

    sell_price = book.at(sym, close_day, 14)
    rows.append(_t(uid, kid, ex, MarketType.SPOT, sym, TradeSide.SELL, sell_price, total, _ts(close_day, 14), f"{tag}-s"))
    return rows

def _fut(book: PriceBook, uid: UUID, kid: UUID, ex: Exchange, sym: str, qty: str,
         open_day: int, close_day: int, want_win: bool, tag: str) -> list[Trade]:
    entry = book.at(sym, open_day, 10)
    exit_price = book.at(sym, close_day, 15)
    quantity = Decimal(qty)

    rises = exit_price > entry
    side = TradeSide.BUY if rises == want_win else TradeSide.SELL
    opp = TradeSide.SELL if side == TradeSide.BUY else TradeSide.BUY
    direction = 1 if side == TradeSide.BUY else -1
    pnl = (exit_price - entry) * quantity * direction

    return [
        _t(uid, kid, ex, MarketType.FUTURES, sym, side, entry, quantity, _ts(open_day, 10), f"{tag}-o"),
        _t(uid, kid, ex, MarketType.FUTURES, sym, opp, exit_price, quantity, _ts(close_day, 15), f"{tag}-c", pnl)
    ]

def _fut_open(book: PriceBook, uid: UUID, kid: UUID, ex: Exchange, sym: str, side: TradeSide,
              qty: str, open_day: int, tag: str) -> list[Trade]:
    price = book.at(sym, open_day, 10)
    return [_t(uid, kid, ex, MarketType.FUTURES, sym, side, price, Decimal(qty), _ts(open_day, 10), f"{tag}-o")]

_SCALP_QTY = {
    "BTCUSDT": "0.05", "ETHUSDT": "0.8", "SOLUSDT": "15", "BNBUSDT": "3", "XRPUSDT": "800",
    "DOGEUSDT": "6000", "ADAUSDT": "2500", "AVAXUSDT": "40", "LINKUSDT": "80", "ARBUSDT": "1800",
    "OPUSDT": "800", "DOTUSDT": "280", "ATOMUSDT": "220", "LTCUSDT": "16", "APTUSDT": "160"
}
_SYMS = tuple(_SCALP_QTY)

def _scalp(book: PriceBook, uid: UUID, kid: UUID, ex: Exchange, sym: str,
           day: int, hour: int, minute: int, hold_min: int, win: bool, tag: str) -> list[Trade]:
    entry = book.at(sym, day, hour)
    frac = Decimal(min(minute + hold_min, 60)) / 60
    move = (book.at(sym, day, hour + 1) - entry) * frac
    floor = entry * Decimal("0.001")
    if abs(move) < floor:
        move = floor if (day * 31 + hour * 7) % 2 == 0 else -floor
    side = TradeSide.BUY if (move > 0) == win else TradeSide.SELL
    direction = 1 if side == TradeSide.BUY else -1
    exit_price = entry + move
    quantity = Decimal(_SCALP_QTY[sym])
    pnl = (exit_price - entry) * quantity * direction
    opp = TradeSide.SELL if side == TradeSide.BUY else TradeSide.BUY
    open_ts = _ts(day, hour, minute)
    close_ts = open_ts + timedelta(minutes=hold_min)
    return [
        _t(uid, kid, ex, MarketType.FUTURES, sym, side, entry, quantity, open_ts, f"{tag}-o"),
        _t(uid, kid, ex, MarketType.FUTURES, sym, opp, exit_price, quantity, close_ts, f"{tag}-c", pnl)
    ]

def _scalps(book: PriceBook, uid: UUID, fut_keys: list[tuple[Exchange, UUID]]) -> list[Trade]:
    rows: list[Trade] = []
    n = 0
    for day in range(1, 58):
        count = (day + 1) % 3 + (1 if day % 4 == 0 else 0)
        for s in range(count):
            ex, kid = fut_keys[(n + s) % len(fut_keys)]
            sym = _SYMS[(n * 2 + day) % len(_SYMS)]
            win = (n * 7 + day) % 7 < 4
            hour = 8 + (n * 3 + s * 5) % 11
            minute = (n * 11) % 45
            hold = 1 + n % 18
            rows += _scalp(book, uid, kid, ex, sym, day, hour, minute, hold, win, f"sc{n}")
            n += 1
    return rows

def _hedges(book: PriceBook, uid: UUID, fut_keys: list[tuple[Exchange, UUID]]) -> list[Trade]:
    rows: list[Trade] = []
    for i, sym in enumerate(_SYMS):
        ex, kid = fut_keys[i % len(fut_keys)]
        open_day = 51 - i * 3
        close_day = open_day - (2 + i % 4)
        rows += _fut(book, uid, kid, ex, sym, _SCALP_QTY[sym], open_day, close_day, i % 3 != 0, f"hg{i}")
    return rows

async def seed_demo_data(session: AsyncSession, http: aiohttp.ClientSession) -> bool:
    if (await session.execute(select(User).where(User.email == DEMO_EMAIL))).scalar_one_or_none():
        return False

    book = await _load_price_book(http)

    session.add(User(
        id=DEMO_USER_ID, email=DEMO_EMAIL, name="Demo",
        password_hash=hash_password("demopass123"), plan=PlanTier.PRO, email_verified=True
    ))
    await session.flush()

    creds = get_config().seed_credentials()
    key_specs = [
        ("binance", Exchange.BINANCE, ["spot", "futures"], "Demo Binance"),
        ("bybit", Exchange.BYBIT, ["spot", "futures"], "Demo Bybit"),
        ("okx", Exchange.OKX, ["spot", "futures"], "Demo Okx"),
        ("bitget1", Exchange.BITGET, ["spot"], "Demo Bitget Spot"),
        ("bitget2", Exchange.BITGET, ["futures"], "Demo Bitget Futures")
    ]

    keys: dict[str, ApiKey] = {}
    for slot, ex, markets, label in key_specs:
        real = creds.get(slot)
        if real:
            raw_key, raw_secret, raw_pass = real
        else:
            raw_key, raw_secret = f"demo-{slot}-key", f"demo-{slot}-secret"
            raw_pass = f"demo-{slot}-pass" if ex in (Exchange.OKX, Exchange.BITGET) else None
        keys[slot] = ApiKey(
            id=uuid4(), user_id=DEMO_USER_ID, exchange=ex,
            api_key_hash=hash_api_key(raw_key), api_key_encrypted=encrypt(raw_key),
            api_secret_encrypted=encrypt(raw_secret),
            passphrase_encrypted=encrypt(raw_pass) if raw_pass else None,
            label=label, capabilities=markets,
            next_check_at=initial_next_check()
        )
        session.add(keys[slot])
    await session.flush()

    uid = DEMO_USER_ID
    binance, bybit, okx = keys["binance"].id, keys["bybit"].id, keys["okx"].id
    bitget_spot, bitget_fut = keys["bitget1"].id, keys["bitget2"].id

    fut_keys = [(Exchange.BINANCE, binance), (Exchange.BYBIT, bybit), (Exchange.OKX, okx), (Exchange.BITGET, bitget_fut)]

    trades: list[Trade] = _scalps(book, uid, fut_keys)
    trades += _hedges(book, uid, fut_keys)

    trades += _spot(book, uid, binance, Exchange.BINANCE, "ETHUSDT", ["0.4", "0.3", "0.3"], [27, 26, 25], 24, "avg-eth")
    trades += _spot(book, uid, bitget_spot, Exchange.BITGET, "SOLUSDT", ["8", "6"], [19, 18], 17, "avg-sol")

    trades += _spot(book, uid, okx, Exchange.OKX, "BTCUSDT", ["0.02"], [12], 12, "spot-btc")
    trades += _spot(book, uid, bitget_spot, Exchange.BITGET, "XRPUSDT", ["500"], [9], 9, "spot-xrp")

    trades += _fut_open(book, uid, bybit, Exchange.BYBIT, "ETHUSDT", TradeSide.BUY, "1.4", 1, "open-eth")
    trades += _fut_open(book, uid, okx, Exchange.OKX, "SOLUSDT", TradeSide.BUY, "22", 2, "open-sol")
    trades += _fut_open(book, uid, binance, Exchange.BINANCE, "BTCUSDT", TradeSide.SELL, "0.04", 0, "open-btc")

    session.add_all(trades)

    universe = {(t.exchange, t.market_type, t.symbol) for t in trades}
    session.add_all([MarketUniverse(exchange=ex, market_type=mt, symbol=sym) for ex, mt, sym in universe])

    await session.commit()
    logger.info(f"[seed] demo user {DEMO_EMAIL} + {len(keys)} keys + {len(trades)} trades + {len(universe)} universe symbols")
    return True

if __name__ == "__main__":
    import asyncio
    from db.session import SessionFactory
    from shared.http import create_rest_session

    async def _main() -> None:
        http = create_rest_session()
        try:
            async with SessionFactory() as session:
                seeded = await seed_demo_data(session, http)
                print(f"seeded={seeded}")
        finally:
            await http.close()

    asyncio.run(_main())
