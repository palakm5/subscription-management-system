from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from app.models.plans import BillingPeriod
from app.models.taxes import TaxType
from app.models.discounts import DiscountType, DiscountScope
from app.models.customers import BillingAddress
from app.core.money import ZERO

# ----------------- VARIANTS & PRODUCTS -----------------
class VariantIn(BaseModel):
    attribute: str
    value: str
    extra_price: Decimal = Field(default=ZERO)

class VariantOut(VariantIn):
    id: str

class ProductCreate(BaseModel):
    name: str
    type: str = "service"
    sales_price: Decimal = Field(default=ZERO, ge=0)
    cost_price: Decimal = Field(default=ZERO, ge=0)
    notes: Optional[str] = None
    tax_ids: List[str] = Field(default_factory=list)
    is_active: bool = True
    variants: List[VariantIn] = Field(default_factory=list)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    sales_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    tax_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    id: str
    name: str
    type: str
    sales_price: Decimal
    cost_price: Decimal
    notes: Optional[str] = None
    tax_ids: List[str]
    is_active: bool
    variants: List[VariantOut]
    created_at: datetime
    updated_at: datetime

# ----------------- PLANS -----------------
class PlanCreate(BaseModel):
    name: str
    price: Decimal = Field(default=ZERO, ge=0)
    billing_period: BillingPeriod = BillingPeriod.MONTHLY
    min_quantity: int = Field(default=1, ge=1)
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    auto_close: bool = False
    closable: bool = True
    pausable: bool = True
    renewable: bool = True
    is_active: bool = True

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    billing_period: Optional[BillingPeriod] = None
    min_quantity: Optional[int] = Field(None, ge=1)
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    auto_close: Optional[bool] = None
    closable: Optional[bool] = None
    pausable: Optional[bool] = None
    renewable: Optional[bool] = None
    is_active: Optional[bool] = None

class PlanResponse(BaseModel):
    id: str
    name: str
    price: Decimal
    billing_period: BillingPeriod
    min_quantity: int
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    auto_close: bool
    closable: bool
    pausable: bool
    renewable: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

# ----------------- TAXES -----------------
class TaxCreate(BaseModel):
    name: str
    type: TaxType = TaxType.PERCENT
    rate: Decimal = Field(default=ZERO, ge=0)
    is_active: bool = True

class TaxUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[TaxType] = None
    rate: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None

class TaxResponse(BaseModel):
    id: str
    name: str
    type: TaxType
    rate: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

# ----------------- DISCOUNTS -----------------
class DiscountCreate(BaseModel):
    name: str
    type: DiscountType = DiscountType.PERCENT
    value: Decimal = Field(default=ZERO, ge=0)
    min_purchase: Optional[Decimal] = Field(None, ge=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = Field(None, ge=1)
    scope: DiscountScope = DiscountScope.SUBSCRIPTION
    product_ids: List[str] = Field(default_factory=list)
    is_active: bool = True

class DiscountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[DiscountType] = None
    value: Optional[Decimal] = Field(None, ge=0)
    min_purchase: Optional[Decimal] = Field(None, ge=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = Field(None, ge=1)
    scope: Optional[DiscountScope] = None
    product_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None

class DiscountResponse(BaseModel):
    id: str
    name: str
    type: DiscountType
    value: Decimal
    min_purchase: Optional[Decimal] = None
    min_quantity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = None
    times_used: int
    scope: DiscountScope
    product_ids: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

# ----------------- QUOTATION TEMPLATES -----------------
class QuotationTemplateLineIn(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = Field(default=1, ge=1)

class QuotationTemplateLineOut(BaseModel):
    product_id: str
    variant_id: Optional[str] = None
    quantity: int

class QuotationTemplateCreate(BaseModel):
    name: str
    validity_days: int = Field(default=30, ge=1)
    plan_id: str
    lines: List[QuotationTemplateLineIn] = Field(default_factory=list)

class QuotationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    validity_days: Optional[int] = Field(None, ge=1)
    plan_id: Optional[str] = None
    lines: Optional[List[QuotationTemplateLineIn]] = None

class QuotationTemplateResponse(BaseModel):
    id: str
    name: str
    validity_days: int
    plan_id: str
    lines: List[QuotationTemplateLineOut]
    created_at: datetime
    updated_at: datetime

# ----------------- CUSTOMERS -----------------
class CustomerCreate(BaseModel):
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_address: BillingAddress = Field(default_factory=BillingAddress)
    tax_id: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[BillingAddress] = None
    tax_id: Optional[str] = None

class CustomerResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_address: BillingAddress
    tax_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
