from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from pydantic import Field, EmailStr
from beanie import Document, Indexed
import pymongo

class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"

class User(Document):
    email: Indexed(str, unique=True)
    password_hash: str
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True
    reset_token_hash: Optional[str] = None
    reset_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True)
        ]
