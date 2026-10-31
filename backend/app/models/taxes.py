from datetime import datetime, timezone
from enum import Enum
from pydantic import Field
from beanie import Document
import pymongo
from app.core.money import ZERO, Money

class TaxType(str, Enum):
    PERCENT = "percent"
    FIXED = "fixed"

class Tax(Document):
    name: str
    type: TaxType = TaxType.PERCENT
    rate: Money = Field(default=ZERO)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "taxes"
        indexes = [
            pymongo.IndexModel([("name", pymongo.ASCENDING)]),
            pymongo.IndexModel([("is_active", pymongo.ASCENDING)])
        ]
