from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.core.deps import require_role
from app.models.users import User
from app.models.products import Product
from app.schemas.catalog import (
    ProductCreate, ProductUpdate, ProductResponse,
    VariantIn, VariantOut
)
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/products", tags=["products"])

def to_product_response(p: Product) -> ProductResponse:
    variants = [
        VariantOut(
            id=v.id,
            attribute=v.attribute,
            value=v.value,
            extra_price=v.extra_price
        ) for v in p.variants
    ]
    return ProductResponse(
        id=str(p.id),
        name=p.name,
        type=p.type,
        sales_price=p.sales_price,
        cost_price=p.cost_price,
        notes=p.notes,
        tax_ids=[str(t) for t in p.tax_ids],
        is_active=p.is_active,
        variants=variants,
        created_at=p.created_at,
        updated_at=p.updated_at
    )

@router.get("", response_model=List[ProductResponse])
async def list_products(
    is_active: Optional[bool] = None,
    q: Optional[str] = None,
    current_user: User = Depends(require_role("admin", "staff"))
):
    products = await CatalogService.list_products(is_active=is_active, q=q)
    return [to_product_response(p) for p in products]

@router.get("/{id}", response_model=ProductResponse)
async def get_product(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    prod = await CatalogService.get_product(id)
    return to_product_response(prod)

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    req: ProductCreate,
    current_user: User = Depends(require_role("admin"))
):
    prod = await CatalogService.create_product(req)
    return to_product_response(prod)

@router.put("/{id}", response_model=ProductResponse)
async def update_product(
    id: str,
    req: ProductUpdate,
    current_user: User = Depends(require_role("admin"))
):
    prod = await CatalogService.update_product(id, req)
    return to_product_response(prod)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    id: str,
    current_user: User = Depends(require_role("admin"))
):
    await CatalogService.delete_product(id)

# Variant endpoints: POST|PUT|DELETE /products/{id}/variants
@router.post("/{id}/variants", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def add_variant(
    id: str,
    req: VariantIn,
    current_user: User = Depends(require_role("admin"))
):
    prod = await CatalogService.add_variant(id, req)
    return to_product_response(prod)

@router.put("/{id}/variants/{variant_id}", response_model=ProductResponse)
async def update_variant(
    id: str,
    variant_id: str,
    req: VariantIn,
    current_user: User = Depends(require_role("admin"))
):
    prod = await CatalogService.update_variant(id, variant_id, req)
    return to_product_response(prod)

@router.delete("/{id}/variants/{variant_id}", response_model=ProductResponse)
async def delete_variant(
    id: str,
    variant_id: str,
    current_user: User = Depends(require_role("admin"))
):
    prod = await CatalogService.delete_variant(id, variant_id)
    return to_product_response(prod)
