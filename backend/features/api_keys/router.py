from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.api_key import ApiKeyRepository
from domain.models import User
from features.api_keys.schemas import ApiKeyIn, ApiKeyOut, ApiKeyUpdate, ApiKeyValidationResult
from features.api_keys.service import client_for_key, confirm_key_valid, ensure_ip_restricted, register_key, remove_key
from features.api_keys.sync import run_initial_sync
from shared.deps import get_current_user, get_session
from shared.exceptions import NotFoundError

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

@router.get("/", response_model=list[ApiKeyOut])
async def list_keys(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> list[ApiKeyOut]:
    keys = await ApiKeyRepository(session).get_all(user.id)
    return [ApiKeyOut.model_validate(k, from_attributes=True) for k in keys]

@router.post("/", response_model=ApiKeyValidationResult, status_code=status.HTTP_201_CREATED)
async def add_key(body: ApiKeyIn, request: Request, background: BackgroundTasks,
                  user: User = Depends(get_current_user),
                  session: AsyncSession = Depends(get_session)) -> ApiKeyValidationResult:
    state = request.app.state
    registered = await register_key(session, state.gateway, state.ws_manager, state.trade_ingester, user=user, body=body)
    background.add_task(
        run_initial_sync, state.ws_manager, state.trade_ingester, state.symbol_cache,
        registered.key, registered.client, user.plan, state.sync_progress
    )
    return ApiKeyValidationResult(
        id=registered.key.id, exchange=registered.key.exchange, capabilities=registered.markets,
        ip_restricted=registered.key.ip_restricted, replaced=registered.superseded,
        message="Key re-validated" if registered.superseded else "Key validated"
    )

@router.get("/{key_id}/sync-progress")
async def sync_progress(key_id: UUID, request: Request, user: User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)) -> dict:
    key = await ApiKeyRepository(session).get_by_id(key_id, user.id)
    if not key:
        raise NotFoundError("API key not found")
    return request.app.state.sync_progress.get(key_id, {"state": "idle"})

@router.post("/{key_id}/recheck", response_model=ApiKeyValidationResult)
async def recheck_key(key_id: UUID, request: Request, background: BackgroundTasks,
                      user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)) -> ApiKeyValidationResult:
    key = await ApiKeyRepository(session).get_by_id(key_id, user.id)
    if not key:
        raise NotFoundError("API key not found")

    state = request.app.state
    client = client_for_key(state.gateway, key)
    caps = await client.validate_credentials()
    ensure_ip_restricted(caps, key.exchange)
    fresh = await confirm_key_valid(session, key, caps)
    if fresh is None:
        raise NotFoundError("API key not found after re-validation")

    background.add_task(
        run_initial_sync, state.ws_manager, state.trade_ingester, state.symbol_cache,
        fresh, client, user.plan, state.sync_progress
    )
    return ApiKeyValidationResult(
        id=fresh.id, exchange=fresh.exchange, capabilities=fresh.capabilities,
        ip_restricted=fresh.ip_restricted, replaced=False, message="Key re-validated"
    )

@router.patch("/{key_id}", response_model=ApiKeyOut)
async def update_key(key_id: UUID, body: ApiKeyUpdate, user: User = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session)) -> ApiKeyOut:
    repo = ApiKeyRepository(session)
    key = await repo.get_by_id(key_id, user.id)
    if not key:
        raise NotFoundError("API key not found")
    await repo.update_label(key, body.label.strip())
    return ApiKeyOut.model_validate(key, from_attributes=True)

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(key_id: UUID, request: Request, user: User = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session)) -> None:
    key = await ApiKeyRepository(session).get_by_id(key_id, user.id)
    if not key:
        raise NotFoundError("API key not found")
    await remove_key(session, request.app.state.ws_manager, request.app.state.trade_ingester, key)
