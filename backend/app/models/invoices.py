from datetime import datetime, date, timezone
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from beanie import Document, Indexed, PydanticObjectId
import pymongo
from app.core.money import ZERO, Money
from app.models.customers import BillingAddress

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"

class CustomerSnapshot(BaseModel):
    name: str
    billing_address: BillingAddress = Field(default_factory=BillingAddress)
    tax_id: Optional[str] = None

class TaxBreakdownItem(BaseModel):
    tax_id: PydanticObjectId
    name: str
    rate: Money = Field(default=ZERO)
    amount: Money = Field(default=ZERO)

class InvoiceLine(BaseModel):
    product_name: str
    variant_label: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    unit_price: Money = Field(default=ZERO)
    discount_amount: Money = Field(default=ZERO)
    tax_breakdown: List[TaxBreakdownItem] = Field(default_factory=list)
    line_total: Money = Field(default=ZERO)

class AppliedDiscount(BaseModel):
    discount_id: PydanticObjectId
    name: str
    amount: Money = Field(default=ZERO)

class Invoice(Document):
    number: Indexed(str, unique=True)
    subscription_id: Indexed(PydanticObjectId)
    customer_id: Indexed(PydanticObjectId)
    customer_snapshot: CustomerSnapshot
    period_start: date
    period_end: date
    issue_date: date
    due_date: date
    status: InvoiceStatus = InvoiceStatus.DRAFT
    lines: List[InvoiceLine] = Field(default_factory=list)
    subtotal: Money = Field(default=ZERO)
    discount_total: Money = Field(default=ZERO)
    tax_total: Money = Field(default=ZERO)
    total: Money = Field(default=ZERO)
    amount_paid: Money = Field(default=ZERO)
    applied_discounts: List[AppliedDiscount] = Field(default_factory=list)
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_overdue(self) -> bool:
        """Overdue is derived, never stored: status == confirmed AND due_date < today AND amount_paid < total."""
        today = date.today()
        return self.status == InvoiceStatus.CONFIRMED and self.due_date < today and self.amount_paid < self.total

    class Settings:
        name = "invoices"
        indexes = [
            pymongo.IndexModel([("number", pymongo.ASCENDING)], unique=True),
            # CRITICAL IDEMPOTENCY GUARD:
            pymongo.IndexModel(
                [
                    ("subscription_id", pymongo.ASCENDING),
                    ("period_start", pymongo.ASCENDING),
                    ("period_end", pymongo.ASCENDING)
                ],
                unique=True
            ),
            pymongo.IndexModel([
                ("customer_id", pymongo.ASCENDING),
                ("status", pymongo.ASCENDING),
                ("due_date", pymongo.ASCENDING)
            ]),
            pymongo.IndexModel([
                ("status", pymongo.ASCENDING),
                ("due_date", pymongo.ASCENDING)
            ])
        ]
