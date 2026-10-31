from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
import pymongo
from app.core.money import ZERO, Money

class Variant(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    attribute: str
    value: str
    extra_price: Money = Field(default=ZERO)

    model_config = {
        "populate_by_name": True
    }

class Product(Document):
    name: str
    type: str = "service"
    sales_price: Money = Field(default=ZERO)
    cost_price: Money = Field(default=ZERO)
    notes: Optional[str] = None
    tax_ids: List[PydanticObjectId] = Field(default_factory=list)
    is_active: bool = True
    variants: List[Variant] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "products"
        indexes = [
            pymongo.IndexModel([("name", pymongo.ASCENDING)]),
            pymongo.IndexModel([("name", pymongo.TEXT)])
        ]
