from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.core.deps import require_role
from app.models.users import User
from app.models.discounts import Discount
from app.schemas.catalog import DiscountCreate, DiscountUpdate, DiscountResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/discounts", tags=["discounts"])

def to_discount_response(d: Discount) -> DiscountResponse:
    return DiscountResponse(
        id=str(d.id),
        name=d.name,
        type=d.type,
        value=d.value,
        min_purchase=d.min_purchase,
        min_quantity=d.min_quantity,
        start_date=d.start_date,
        end_date=d.end_date,
        usage_limit=d.usage_limit,
        times_used=d.times_used,
        scope=d.scope,
        product_ids=[str(pid) for pid in d.product_ids],
        is_active=d.is_active,
        created_at=d.created_at,
        updated_at=d.updated_at
    )

@router.get("", response_model=List[DiscountResponse])
async def list_discounts(
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_role("admin", "staff"))
):
    discounts = await CatalogService.list_discounts(is_active=is_active)
    return [to_discount_response(d) for d in discounts]

@router.get("/{id}", response_model=DiscountResponse)
async def get_discount(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    disc = await CatalogService.get_discount(id)
    return to_discount_response(disc)

@router.post("", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
async def create_discount(
    req: DiscountCreate,
    current_user: User = Depends(require_role("admin"))
):
    disc = await CatalogService.create_discount(req)
    return to_discount_response(disc)

@router.put("/{id}", response_model=DiscountResponse)
async def update_discount(
    id: str,
    req: DiscountUpdate,
    current_user: User = Depends(require_role("admin"))
):
    disc = await CatalogService.update_discount(id, req)
    return to_discount_response(disc)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discount(
    id: str,
    current_user: User = Depends(require_role("admin"))
):
    await CatalogService.delete_discount(id)
