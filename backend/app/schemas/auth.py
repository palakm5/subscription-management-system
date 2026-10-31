from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.models.users import UserRole
from app.models.customers import BillingAddress

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: Optional[str] = None
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[BillingAddress] = None
    tax_id: Optional[str] = None

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower().strip()

    @model_validator(mode="after")
    def verify_passwords_match(self):
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower().strip()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower().strip()

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

class CustomerResponse(BaseModel):
    id: str
    user_id: str
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_address: BillingAddress
    tax_id: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    customer: Optional[CustomerResponse] = None

class MessageResponse(BaseModel):
    message: str

class CreateStaffRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower().strip()
