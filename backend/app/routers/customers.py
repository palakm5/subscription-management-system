from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.deps import require_role
from app.core.pagination import PaginatedResponse
from app.models.users import User
from app.models.customers import Customer
from app.schemas.catalog import (
    CustomerCreate, CustomerUpdate, CustomerResponse
)
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/customers", tags=["customers"])

def to_customer_response(c: Customer) -> CustomerResponse:
    return CustomerResponse(
        id=str(c.id),
        user_id=str(c.user_id) if c.user_id else None,
        name=c.name,
        company=c.company,
        phone=c.phone,
        billing_address=c.billing_address,
        tax_id=c.tax_id,
        created_at=c.created_at,
        updated_at=c.updated_at
    )

@router.get("", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: Optional[str] = None,
    current_user: User = Depends(require_role("admin", "staff"))
):
    customers, total = await CatalogService.list_customers(page=page, page_size=page_size, q=q)
    items = [to_customer_response(c) for c in customers]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{id}", response_model=CustomerResponse)
async def get_customer(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    cust = await CatalogService.get_customer(id)
    return to_customer_response(cust)

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    req: CustomerCreate,
    current_user: User = Depends(require_role("admin", "staff"))
):
    cust = await CatalogService.create_customer(req)
    return to_customer_response(cust)

@router.put("/{id}", response_model=CustomerResponse)
async def update_customer(
    id: str,
    req: CustomerUpdate,
    current_user: User = Depends(require_role("admin", "staff"))
):
    cust = await CatalogService.update_customer(id, req)
    return to_customer_response(cust)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    await CatalogService.delete_customer(id)
