from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.invoices import InvoiceStatus, CustomerSnapshot
from app.core.money import ZERO

class TaxBreakdownItemOut(BaseModel):
    tax_id: str
    name: str
    rate: Decimal
    amount: Decimal

class InvoiceLineOut(BaseModel):
    product_name: str
    variant_label: Optional[str] = None
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    tax_breakdown: List[TaxBreakdownItemOut]
    line_total: Decimal

class AppliedDiscountOut(BaseModel):
    discount_id: str
    name: str
    amount: Decimal

class InvoiceResponse(BaseModel):
    id: str
    number: str
    subscription_id: str
    customer_id: str
    customer_snapshot: CustomerSnapshot
    period_start: date
    period_end: date
    issue_date: date
    due_date: date
    status: InvoiceStatus
    is_overdue: bool
    lines: List[InvoiceLineOut]
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    applied_discounts: List[AppliedDiscountOut]
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
