from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.subscriptions import SubscriptionStatus
from app.core.money import ZERO

class SubscriptionLineIn(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=0) # If omitted, auto-calculated from product+variant

class SubscriptionLineOut(BaseModel):
    line_id: str
    product_id: str
    product_name: str
    variant_id: Optional[str] = None
    variant_label: Optional[str] = None
    quantity: int
    unit_price: Decimal
    tax_ids: List[str]
    amount: Decimal

class StatusHistoryOut(BaseModel):
    from_status: Optional[str] = Field(None, alias="from")
    to_status: str = Field(..., alias="to")
    by: str
    at: datetime

    model_config = {
        "populate_by_name": True
    }

class SubscriptionCreate(BaseModel):
    customer_id: str
    plan_id: Optional[str] = None # Optional if template_id is provided
    template_id: Optional[str] = None
    start_date: Optional[date] = None # Defaults to today
    expiry_date: Optional[date] = None # Auto-computed from plan period if omitted
    payment_terms: int = Field(default=15, ge=0)
    lines: Optional[List[SubscriptionLineIn]] = None
    discount_ids: List[str] = Field(default_factory=list)

class SubscriptionUpdate(BaseModel):
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    payment_terms: Optional[int] = Field(None, ge=0)
    quotation_valid_until: Optional[date] = None
    lines: Optional[List[SubscriptionLineIn]] = None
    discount_ids: Optional[List[str]] = None

class SubscriptionTransitionRequest(BaseModel):
    to: str

class SubscriptionResponse(BaseModel):
    id: str
    number: str
    customer_id: str
    plan_id: str
    template_id: Optional[str] = None
    status: SubscriptionStatus
    start_date: date
    expiry_date: date
    payment_terms: int
    quotation_valid_until: Optional[date] = None
    next_invoice_date: Optional[date] = None
    lines: List[SubscriptionLineOut]
    discount_ids: List[str]
    status_history: List[StatusHistoryOut]
    created_at: datetime
    updated_at: datetime
