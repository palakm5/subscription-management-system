from datetime import datetime, date, timezone
from typing import Optional
from enum import Enum
from pydantic import Field
from beanie import Document, Indexed, PydanticObjectId
import pymongo
from app.core.money import ZERO, Money

class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    CHEQUE = "cheque"
    OTHER = "other"

class Payment(Document):
    invoice_id: Indexed(PydanticObjectId)
    customer_id: Indexed(PydanticObjectId)
    method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    amount: Money = Field(default=ZERO)
    paid_on: date = Field(default_factory=date.today)
    note: Optional[str] = None
    recorded_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "payments"
        indexes = [
            pymongo.IndexModel([("invoice_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("paid_on", pymongo.ASCENDING)])
        ]
