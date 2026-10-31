from typing import List
from fastapi import APIRouter, Depends, status

from app.core.deps import require_role
from app.models.users import User
from app.models.quotation_templates import QuotationTemplate
from app.schemas.catalog import (
    QuotationTemplateCreate, QuotationTemplateUpdate,
    QuotationTemplateResponse, QuotationTemplateLineOut
)
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/quotation-templates", tags=["quotation-templates"])

def to_template_response(t: QuotationTemplate) -> QuotationTemplateResponse:
    lines = [
        QuotationTemplateLineOut(
            product_id=str(l.product_id),
            variant_id=l.variant_id,
            quantity=l.quantity
        ) for l in t.lines
    ]
    return QuotationTemplateResponse(
        id=str(t.id),
        name=t.name,
        validity_days=t.validity_days,
        plan_id=str(t.plan_id),
        lines=lines,
        created_at=t.created_at,
        updated_at=t.updated_at
    )

@router.get("", response_model=List[QuotationTemplateResponse])
async def list_templates(
    current_user: User = Depends(require_role("admin", "staff"))
):
    templates = await CatalogService.list_templates()
    return [to_template_response(t) for t in templates]

@router.get("/{id}", response_model=QuotationTemplateResponse)
async def get_template(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    tpl = await CatalogService.get_template(id)
    return to_template_response(tpl)

@router.post("", response_model=QuotationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    req: QuotationTemplateCreate,
    current_user: User = Depends(require_role("admin"))
):
    tpl = await CatalogService.create_template(req)
    return to_template_response(tpl)

@router.put("/{id}", response_model=QuotationTemplateResponse)
async def update_template(
    id: str,
    req: QuotationTemplateUpdate,
    current_user: User = Depends(require_role("admin"))
):
    tpl = await CatalogService.update_template(id, req)
    return to_template_response(tpl)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    id: str,
    current_user: User = Depends(require_role("admin"))
):
    await CatalogService.delete_template(id)
