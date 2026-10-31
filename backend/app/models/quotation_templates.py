from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
import pymongo

class QuotationTemplateLine(BaseModel):
    product_id: PydanticObjectId
    variant_id: Optional[str] = None
    quantity: int = Field(default=1, ge=1)

class QuotationTemplate(Document):
    name: str
    validity_days: int = Field(default=30, ge=1)
    plan_id: PydanticObjectId
    lines: List[QuotationTemplateLine] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "quotation_templates"
        indexes = [
            pymongo.IndexModel([("name", pymongo.ASCENDING)])
        ]
