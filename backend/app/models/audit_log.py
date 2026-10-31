from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import Field
from beanie import Document, Indexed, PydanticObjectId
import pymongo

class AuditLog(Document):
    actor_id: str
    entity: str
    entity_id: str
    action: str
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "audit_log"
        indexes = [
            pymongo.IndexModel([("entity", pymongo.ASCENDING), ("entity_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("at", pymongo.DESCENDING)])
        ]
