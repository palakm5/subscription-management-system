from datetime import datetime, date, timezone
from typing import List, Optional
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel, Field
from beanie import Document, Indexed, PydanticObjectId
import pymongo
from app.core.money import ZERO, Money

class SubscriptionStatus(str, Enum):
    DRAFT = "draft"
    QUOTATION = "quotation"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"

class SubscriptionLine(BaseModel):
    line_id: str = Field(default_factory=lambda: str(ObjectId()))
    product_id: PydanticObjectId
    product_name: str
    variant_id: Optional[str] = None
    variant_label: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    unit_price: Money = Field(default=ZERO)
    tax_ids: List[PydanticObjectId] = Field(default_factory=list)
    amount: Money = Field(default=ZERO)

class StatusHistoryEntry(BaseModel):
    from_status: Optional[str] = Field(None, alias="from")
    to_status: str = Field(..., alias="to")
    by: str
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True
    }

class Subscription(Document):
    number: Indexed(str, unique=True)
    customer_id: Indexed(PydanticObjectId)
    plan_id: PydanticObjectId
    template_id: Optional[PydanticObjectId] = None
    status: SubscriptionStatus = SubscriptionStatus.DRAFT
    start_date: date
    expiry_date: date
    payment_terms: int = Field(default=15, ge=0)
    quotation_valid_until: Optional[date] = None
    next_invoice_date: Optional[date] = None
    lock_until: Optional[datetime] = None
    locked_by: Optional[str] = None
    lines: List[SubscriptionLine] = Field(default_factory=list)
    discount_ids: List[PydanticObjectId] = Field(default_factory=list)
    status_history: List[StatusHistoryEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "subscriptions"
        indexes = [
            pymongo.IndexModel([("number", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("status", pymongo.ASCENDING), ("next_invoice_date", pymongo.ASCENDING)]),
            pymongo.IndexModel([("customer_id", pymongo.ASCENDING), ("status", pymongo.ASCENDING)]),
            pymongo.IndexModel([("status", pymongo.ASCENDING), ("expiry_date", pymongo.ASCENDING)])
        ]
