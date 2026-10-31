from datetime import datetime, date, timezone
from typing import Optional
from enum import Enum
from pydantic import Field
from beanie import Document
import pymongo
from app.core.money import ZERO, Money

class BillingPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Plan(Document):
    name: str
    price: Money = Field(default=ZERO)
    billing_period: BillingPeriod = BillingPeriod.MONTHLY
    min_quantity: int = Field(default=1, ge=1)
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    auto_close: bool = False
    closable: bool = True
    pausable: bool = True
    renewable: bool = True
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "plans"
        indexes = [
            pymongo.IndexModel([("name", pymongo.ASCENDING)]),
            pymongo.IndexModel([("is_active", pymongo.ASCENDING)])
        ]
