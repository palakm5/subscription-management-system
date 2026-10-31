from typing import List, Optional
from fastapi import APIRouter, Depends, status

from app.core.deps import require_role
from app.models.users import User
from app.models.plans import Plan
from app.schemas.catalog import PlanCreate, PlanUpdate, PlanResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/plans", tags=["plans"])

def to_plan_response(p: Plan) -> PlanResponse:
    return PlanResponse(
        id=str(p.id),
        name=p.name,
        price=p.price,
        billing_period=p.billing_period,
        min_quantity=p.min_quantity,
        available_from=p.available_from,
        available_to=p.available_to,
        auto_close=p.auto_close,
        closable=p.closable,
        pausable=p.pausable,
        renewable=p.renewable,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at
    )

@router.get("", response_model=List[PlanResponse])
async def list_plans(
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_role("admin", "staff"))
):
    plans = await CatalogService.list_plans(is_active=is_active)
    return [to_plan_response(p) for p in plans]

@router.get("/{id}", response_model=PlanResponse)
async def get_plan(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    plan = await CatalogService.get_plan(id)
    return to_plan_response(plan)

@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    req: PlanCreate,
    current_user: User = Depends(require_role("admin"))
):
    plan = await CatalogService.create_plan(req)
    return to_plan_response(plan)

@router.put("/{id}", response_model=PlanResponse)
async def update_plan(
    id: str,
    req: PlanUpdate,
    current_user: User = Depends(require_role("admin"))
):
    plan = await CatalogService.update_plan(id, req)
    return to_plan_response(plan)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    id: str,
    current_user: User = Depends(require_role("admin"))
):
    await CatalogService.delete_plan(id)
