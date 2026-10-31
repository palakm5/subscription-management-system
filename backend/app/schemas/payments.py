from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from app.models.payments import PaymentMethod
from app.core.money import ZERO

class PaymentCreate(BaseModel):
    method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    amount: Decimal = Field(..., gt=0, description="Payment amount must be greater than zero")
    paid_on: Optional[date] = None
    note: Optional[str] = None

class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    customer_id: str
    method: PaymentMethod
    amount: Decimal
    paid_on: date
    note: Optional[str] = None
    recorded_by: str
    created_at: datetime
    updated_at: datetime
