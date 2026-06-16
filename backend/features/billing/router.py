import json

import stripe

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models import User
from features.billing import service
from features.billing.schemas import CheckoutIn, CheckoutOut, InvoiceOut, PortalOut, SubscriptionOut
from shared.deps import get_current_user, get_session
from shared.exceptions import BadRequestError

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/checkout", response_model=CheckoutOut)
async def checkout(body: CheckoutIn, user: User = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session)) -> CheckoutOut:
    return await service.create_checkout(session, user, body.cycle)

@router.post("/portal", response_model=PortalOut)
async def portal(user: User = Depends(get_current_user)) -> PortalOut:
    return await service.create_portal(user)

@router.get("/subscription", response_model=SubscriptionOut)
async def subscription(request: Request, user: User = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)) -> SubscriptionOut:
    await service.sync_if_stale(session, request.app.state.ws_manager, user)
    return service.subscription_view(user)

@router.get("/invoices", response_model=list[InvoiceOut])
async def invoices(user: User = Depends(get_current_user)) -> list[InvoiceOut]:
    return await service.list_invoices(user)

@router.post("/webhook")
async def webhook(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        service.construct_event(payload, signature)
    except ValueError:
        raise BadRequestError("Invalid webhook payload")
    except stripe.SignatureVerificationError:
        raise BadRequestError("Invalid webhook signature")
    await service.handle_event(json.loads(payload), session, request.app.state.ws_manager)
    return {"received": True}
