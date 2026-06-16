from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.api_key import ApiKeyRepository
from db.repositories.event import EventRepository
from db.repositories.positions import PositionsRepository
from db.repositories.trade import TradeRepository
from domain.config import get_config
from domain.enums import Exchange, MarketType, PlanTier
from domain.models import ApiKey, User
from domain.plans import get_plan
from exchanges.client import BaseExchangeClient
from exchanges.gateway import ExchangeGateway
from exchanges.key_format import validate_key_format
from exchanges.types import KeyCapabilities
from exchanges.ws_manager import WebSocketManager
from features.api_keys.schemas import ApiKeyIn, SUSPENDED_BY_PLAN
from features.trades.ingester import TradeIngester
from shared.exceptions import DuplicateKeyError, IpNotRestrictedError, KeyAccessRestrictedError, PlanLimitError
from shared.security import decrypt, encrypt, hash_api_key
from utils.logger import logger

RECHECK_INTERVAL = timedelta(minutes=10)

@dataclass(frozen=True, slots=True)
class RegisteredKey:
    key: ApiKey
    client: BaseExchangeClient
    markets: list[str]
    superseded: bool

def client_for_key(gateway: ExchangeGateway, key: ApiKey) -> BaseExchangeClient:
    return gateway.client(
        key.exchange, decrypt(key.api_key_encrypted), decrypt(key.api_secret_encrypted),
        passphrase=decrypt(key.passphrase_encrypted) if key.passphrase_encrypted else None
    )

async def default_label(repo: ApiKeyRepository, user_id: UUID, exchange: Exchange) -> str:
    count = await repo.count_by_exchange(user_id, exchange)
    return exchange.label if count == 0 else f"{exchange.label} {count + 1}"

def account_market_coverage(existing: Sequence[ApiKey], requested_markets: list[str], exchange: Exchange) -> list[ApiKey]:
    requested = set(requested_markets)
    covered_ok = {m for k in existing if k.last_error is None for m in k.capabilities}

    conflict = requested & covered_ok
    if conflict:
        addable = requested - covered_ok
        if addable:
            raise KeyAccessRestrictedError(
                f"{exchange.label}: {', '.join(sorted(conflict))} already connected on this account — "
                f"select only {', '.join(sorted(addable))} for this key"
            )
        raise DuplicateKeyError(f"{exchange.label}: this account is already connected for {', '.join(sorted(requested))}")

    return [k for k in existing if k.last_error is not None and set(k.capabilities) & requested]

async def register_key(session: AsyncSession, gateway: ExchangeGateway, ws_mgr: WebSocketManager,
                       ingester: TradeIngester, *, user: User, body: ApiKeyIn) -> RegisteredKey:
    repo = ApiKeyRepository(session)
    validate_key_format(body.exchange, body.api_key, body.api_secret, body.passphrase)
    key_hash = hash_api_key(body.api_key)
    if await repo.exists_by_hash(user.id, key_hash):
        raise DuplicateKeyError("This API key is already connected")

    client = gateway.client(body.exchange, body.api_key, body.api_secret, passphrase=body.passphrase)
    caps = await client.validate_credentials()
    ensure_ip_restricted(caps, body.exchange)
    markets = resolve_markets(caps, body)

    existing = await repo.find_all_by_account(user.id, body.exchange, caps.account_uid) if caps.account_uid else []
    superseded = account_market_coverage(existing, markets, body.exchange)
    await ensure_plan_capacity(repo, user, bool(superseded))

    label = (body.label or "").strip() or (superseded[0].label if superseded else None) or await default_label(repo, user.id, body.exchange)
    key = repo.add(
        user_id=user.id, exchange=body.exchange,
        api_key_encrypted=encrypt(body.api_key),
        api_secret_encrypted=encrypt(body.api_secret), api_key_hash=key_hash,
        passphrase_encrypted=encrypt(body.passphrase) if body.passphrase else None,
        label=label, capabilities=markets, account_uid=caps.account_uid,
        ip_restricted=caps.ip_restricted
    )
    await session.flush()

    trade_repo = TradeRepository(session)
    positions_repo = PositionsRepository(session)
    requested = set(markets)
    for old in superseded:
        kept = [MarketType(m) for m in old.capabilities if m in requested]
        await trade_repo.reassign(old.id, key.id, kept)
        await positions_repo.reassign_key(old.id, key.id, kept)
        await repo.remove(old)
    await session.commit()
    await session.refresh(key)

    for old in superseded:
        await ws_mgr.disconnect(old.id, persist_status=False)
        ingester.forget(old.id)

    if not superseded:
        await EventRepository(session).record("key_added", user.id, {"exchange": body.exchange.value, "markets": markets})

    logger.info(
        f"[api-keys] registered {body.exchange.value} key={key.id} markets={markets} "
        f"ip_restricted={caps.ip_restricted} superseded={len(superseded)}"
    )
    return RegisteredKey(key=key, client=client, markets=markets, superseded=bool(superseded))

def ensure_ip_restricted(caps: KeyCapabilities, exchange: Exchange) -> None:
    if not get_config().proxy_pool or caps.ip_restricted:
        return
    raise IpNotRestrictedError(
        f"{exchange.label}: this key has no IP whitelist — add {get_config().whitelist_hint} to the key's "
        f"IP restriction on {exchange.label}, then retry"
    )

def resolve_markets(caps: KeyCapabilities, body: ApiKeyIn) -> list[str]:
    available = caps.as_list()
    requested = {m.value for m in body.markets}
    if not requested:
        return available

    missing = requested - set(available)
    if missing:
        raise KeyAccessRestrictedError(
            f"This key can't access {', '.join(sorted(missing))} on {body.exchange.value} — "
            f"recreate it with those markets, or unselect them"
        )
    return sorted(requested)

async def ensure_plan_capacity(repo: ApiKeyRepository, user: User, replacing: bool) -> None:
    if replacing:
        return
    plan = get_plan(user.plan)
    if plan.api_keys_limit is not None and await repo.count_for_user(user.id) >= plan.api_keys_limit:
        raise PlanLimitError(
            f"Free plan allows up to {plan.api_keys_limit} API keys — upgrade to Pro for unlimited connections"
        )

async def apply_plan_to_keys(session: AsyncSession, ws_mgr: WebSocketManager, user: User, tier: PlanTier) -> None:
    repo = ApiKeyRepository(session)
    keys = sorted(await repo.get_all(user.id), key=lambda k: k.created_at)
    limit = get_plan(tier).api_keys_limit
    allowed = len(keys) if limit is None else limit

    for key in keys[allowed:]:
        if key.last_error != SUSPENDED_BY_PLAN:
            await ws_mgr.disconnect(key.id, persist_status=False)
            await repo.set_last_error(key.id, SUSPENDED_BY_PLAN)
            logger.info(f"[api-keys] suspended {key.exchange.value} key={key.id} (plan limit)")

    now = datetime.now(timezone.utc)
    for key in keys[:allowed]:
        if key.last_error == SUSPENDED_BY_PLAN:
            await repo.mark_checked(key.id, now, None)
            logger.info(f"[api-keys] reactivated {key.exchange.value} key={key.id} — gap sync will follow")

async def confirm_key_valid(session: AsyncSession, key: ApiKey, caps: KeyCapabilities) -> ApiKey | None:
    repo = ApiKeyRepository(session)
    if key.last_error is not None and key.last_error != SUSPENDED_BY_PLAN:
        logger.info(f"[api-keys] {key.exchange.value} key={key.id} recovered — error cleared")
    available = set(caps.as_list())
    if not set(key.capabilities).issubset(available):
        kept = sorted(set(key.capabilities) & available)
        logger.info(f"[api-keys] {key.id} capabilities narrowed to {kept} after re-validation")
        await repo.update_capabilities(key.id, kept)
    await repo.mark_checked(
        key.id, datetime.now(timezone.utc) + RECHECK_INTERVAL, None,
        ip_restricted=caps.ip_restricted, account_uid=caps.account_uid
    )
    return await repo.get_global(key.id)

async def remove_key(session: AsyncSession, ws_mgr: WebSocketManager, ingester: TradeIngester, key: ApiKey) -> None:
    await ws_mgr.disconnect(key.id, persist_status=False)
    ingester.forget(key.id)
    await ApiKeyRepository(session).delete(key)
    ingester.touch(key.user_id)
    logger.info(f"[api-keys] deleted {key.exchange.value} key={key.id}")
