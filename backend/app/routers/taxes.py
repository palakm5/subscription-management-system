from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.core.deps import require_role
from app.models.users import User
from app.models.taxes import Tax
from app.schemas.catalog import TaxCreate, TaxUpdate, TaxResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/taxes", tags=["taxes"])

def to_tax_response(t: Tax) -> TaxResponse:
    return TaxResponse(
        id=str(t.id),
        name=t.name,
        type=t.type,
        rate=t.rate,
        is_active=t.is_active,
        created_at=t.created_at,
        updated_at=t.updated_at
    )

@router.get("", response_model=List[TaxResponse])
async def list_taxes(
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_role("admin", "staff"))
):
    taxes = await CatalogService.list_taxes(is_active=is_active)
    return [to_tax_response(t) for t in taxes]

@router.get("/{id}", response_model=TaxResponse)
async def get_tax(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    tax = await CatalogService.get_tax(id)
    return to_tax_response(tax)

@router.post("", response_model=TaxResponse, status_code=status.HTTP_201_CREATED)
async def create_tax(
    req: TaxCreate,
    current_user: User = Depends(require_role("admin"))
):
    tax = await CatalogService.create_tax(req)
    return to_tax_response(tax)

@router.put("/{id}", response_model=TaxResponse)
async def update_tax(
    id: str,
    req: TaxUpdate,
    current_user: User = Depends(require_role("admin"))
):
    tax = await CatalogService.update_tax(id, req)
    return to_tax_response(tax)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tax(
    id: str,
    current_user: User = Depends(require_role("admin"))
):
    await CatalogService.delete_tax(id)
