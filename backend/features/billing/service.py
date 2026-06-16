import asyncio, json, uuid

from datetime import datetime, timezone

import stripe

from db.repositories.user import UserRepository
from domain.config import get_config
from domain.enums import PlanTier
from domain.models import User
from domain.plans import ACTIVE_SUBSCRIPTION_STATUSES
from features.api_keys.service import apply_plan_to_keys
from features.billing.schemas import CheckoutOut, InvoiceOut, PortalOut, SubscriptionOut
from shared.exceptions import BadRequestError, ConflictError
from utils.logger import logger

def _stripe():
    cfg = get_config()
    if not cfg.stripe_secret_key:
        raise BadRequestError("Billing is not configured")
    stripe.api_key = cfg.stripe_secret_key
    return stripe

def _to_dict(stripe_obj) -> dict:
    return json.loads(str(stripe_obj))

async def ensure_customer(session, user: User) -> str:
    if user.stripe_customer_id:
        return user.stripe_customer_id
    api = _stripe()
    customer = await asyncio.to_thread(
        api.Customer.create, email=user.email, name=user.name, metadata={"user_id": str(user.id)}
    )
    await UserRepository(session).set_billing(user, customer_id=customer.id)
    return customer.id

async def create_checkout(session, user: User, cycle: str) -> CheckoutOut:
    cfg = get_config()
    price = {"monthly": cfg.stripe_price_pro_monthly, "yearly": cfg.stripe_price_pro_yearly}.get(cycle)
    if not price:
        raise BadRequestError("This billing cycle is not available")
    api = _stripe()
    customer_id = await ensure_customer(session, user)
    checkout = await asyncio.to_thread(
        api.checkout.Session.create,
        mode="subscription",
        customer=customer_id,
        client_reference_id=str(user.id),
        line_items=[{"price": price, "quantity": 1}],
        subscription_data={"metadata": {"user_id": str(user.id)}},
        success_url=f"{cfg.frontend_url}/dashboard/settings",
        cancel_url=f"{cfg.frontend_url}/dashboard/settings",
        allow_promotion_codes=True
    )
    return CheckoutOut(url=checkout.url)

async def cancel_subscription_now(user: User) -> None:
    if not user.stripe_subscription_id or not get_config().stripe_secret_key:
        return
    api = _stripe()
    try:
        await asyncio.to_thread(api.Subscription.cancel, user.stripe_subscription_id)
        logger.info(f"[billing] subscription cancelled immediately for {user.email}")
    except stripe.StripeError as e:
        logger.warning(f"[billing] immediate cancel failed for {user.email}: {e}")

async def create_portal(user: User) -> PortalOut:
    if not user.stripe_customer_id:
        raise ConflictError("No billing account yet — start a subscription first")
    api = _stripe()
    portal = await asyncio.to_thread(
        api.billing_portal.Session.create,
        customer=user.stripe_customer_id,
        return_url=f"{get_config().frontend_url}/dashboard/settings"
    )
    return PortalOut(url=portal.url)

async def list_invoices(user: User) -> list[InvoiceOut]:
    if not user.stripe_customer_id:
        return []
    api = _stripe()
    result = await asyncio.to_thread(api.Invoice.list, customer=user.stripe_customer_id, limit=24)
    invoices = [_to_dict(inv) for inv in result.data]
    return [
        InvoiceOut(
            id=inv["id"],
            number=inv.get("number"),
            created=datetime.fromtimestamp(inv["created"], tz=timezone.utc),
            amount_paid=inv.get("amount_paid") or 0,
            currency=(inv.get("currency") or "usd").upper(),
            status=inv.get("status"),
            invoice_pdf=inv.get("invoice_pdf"),
            hosted_invoice_url=inv.get("hosted_invoice_url")
        )
        for inv in invoices
    ]

def subscription_view(user: User) -> SubscriptionOut:
    return SubscriptionOut(
        plan=user.plan,
        status=user.subscription_status,
        current_period_end=user.current_period_end,
        cancel_at_period_end=user.cancel_at_period_end,
        has_billing=user.stripe_customer_id is not None,
        billing_enabled=get_config().billing_enabled
    )

def construct_event(payload: bytes, signature: str):
    return stripe.Webhook.construct_event(payload, signature, get_config().stripe_webhook_secret)

async def handle_event(event, session, ws_manager) -> None:
    etype = event.get("type")
    obj = event["data"]["object"]
    users = UserRepository(session)

    if etype == "checkout.session.completed":
        uid = obj.get("client_reference_id")
        if not uid:
            return
        user = await users.get_by_id(uuid.UUID(uid))
        if user is None:
            return
        await users.set_billing(user, customer_id=obj.get("customer"), subscription_id=obj.get("subscription"))
        sub = await _retrieve_subscription(obj.get("subscription"))
        if sub is not None:
            await apply_subscription_state(session, ws_manager, user, sub)

    elif etype in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
        customer_id = obj.get("customer")
        user = await users.get_by_stripe_customer_id(customer_id) if customer_id else None
        if user is None:
            return
        sub = await _retrieve_subscription(obj.get("id"))
        if sub is not None:
            await apply_subscription_state(session, ws_manager, user, sub)

async def apply_subscription_state(session, ws_manager, user: User, sub) -> None:
    status = sub.get("status")
    tier = PlanTier.PRO if status in ACTIVE_SUBSCRIPTION_STATUSES else PlanTier.FREE
    repo = UserRepository(session)
    await repo.set_billing(
        user,
        subscription_id=sub.get("id"),
        status=status,
        current_period_end=_period_end(sub),
        cancel_at_period_end=bool(sub.get("cancel_at_period_end"))
    )
    if user.plan != tier:
        await repo.set_plan(user, tier)
        await apply_plan_to_keys(session, ws_manager, user, tier)
    logger.info(f"[billing] {user.email} subscription {status} → {tier.value}")

async def _retrieve_subscription(subscription_id):
    if not subscription_id:
        return None
    api = _stripe()
    return _to_dict(await asyncio.to_thread(api.Subscription.retrieve, subscription_id))

async def sync_if_stale(session, ws_manager, user: User) -> None:
    if not user.stripe_customer_id or user.subscription_status is not None:
        return
    api = _stripe()
    result = await asyncio.to_thread(api.Subscription.list, customer=user.stripe_customer_id, status="all", limit=1)
    data = _to_dict(result).get("data") or []
    if data:
        await apply_subscription_state(session, ws_manager, user, data[0])

def _period_end(sub):
    items = (sub.get("items") or {}).get("data") or []
    ts = items[0].get("current_period_end") if items else None
    if ts is None:
        ts = sub.get("current_period_end")
    return datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
