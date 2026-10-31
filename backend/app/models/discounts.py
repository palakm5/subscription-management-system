from datetime import datetime, date, timezone
from typing import List, Optional
from enum import Enum
from pydantic import Field
from beanie import Document, PydanticObjectId
import pymongo
from app.core.money import ZERO, Money, OptionalMoney

class DiscountType(str, Enum):
    FIXED = "fixed"
    PERCENT = "percent"

class DiscountScope(str, Enum):
    PRODUCT = "product"
    SUBSCRIPTION = "subscription"

class Discount(Document):
    name: str
    type: DiscountType = DiscountType.PERCENT
    value: Money = Field(default=ZERO)
    min_purchase: OptionalMoney = None
    min_quantity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = None
    times_used: int = Field(default=0, ge=0)
    scope: DiscountScope = DiscountScope.SUBSCRIPTION
    product_ids: List[PydanticObjectId] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "discounts"
        indexes = [
            pymongo.IndexModel([("name", pymongo.ASCENDING)]),
            pymongo.IndexModel([
                ("is_active", pymongo.ASCENDING),
                ("start_date", pymongo.ASCENDING),
                ("end_date", pymongo.ASCENDING)
            ])
        ]
