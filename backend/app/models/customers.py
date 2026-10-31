from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
import pymongo

class BillingAddress(BaseModel):
    line1: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    country: str = ""

class Customer(Document):
    user_id: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId)
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_address: BillingAddress = Field(default_factory=BillingAddress)
    tax_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "customers"
        indexes = [
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)], unique=True, sparse=True),
            pymongo.IndexModel([("name", pymongo.ASCENDING)])
        ]
