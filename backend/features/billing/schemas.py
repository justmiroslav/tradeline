from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

from domain.enums import PlanTier

class CheckoutIn(BaseModel):
    cycle: Literal["monthly", "yearly"]

class CheckoutOut(BaseModel):
    url: str

class PortalOut(BaseModel):
    url: str

class SubscriptionOut(BaseModel):
    plan: PlanTier
    status: Optional[str]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    has_billing: bool
    billing_enabled: bool

class InvoiceOut(BaseModel):
    id: str
    number: Optional[str]
    created: datetime
    amount_paid: int
    currency: str
    status: Optional[str]
    invoice_pdf: Optional[str]
    hosted_invoice_url: Optional[str]
