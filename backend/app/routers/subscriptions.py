from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.deps import require_role
from app.core.pagination import PaginatedResponse
from app.models.users import User
from app.models.subscriptions import Subscription
from app.schemas.subscriptions import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionTransitionRequest,
    SubscriptionResponse, SubscriptionLineOut, StatusHistoryOut
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

def to_subscription_response(s: Subscription) -> SubscriptionResponse:
    lines = [
        SubscriptionLineOut(
            line_id=l.line_id,
            product_id=str(l.product_id),
            product_name=l.product_name,
            variant_id=l.variant_id,
            variant_label=l.variant_label,
            quantity=l.quantity,
            unit_price=l.unit_price,
            tax_ids=[str(t) for t in l.tax_ids],
            amount=l.amount
        ) for l in s.lines
    ]
    history = [
        StatusHistoryOut(
            from_status=h.from_status,
            to_status=h.to_status,
            by=h.by,
            at=h.at
        ) for h in s.status_history
    ]
    return SubscriptionResponse(
        id=str(s.id),
        number=s.number,
        customer_id=str(s.customer_id),
        plan_id=str(s.plan_id),
        template_id=str(s.template_id) if s.template_id else None,
        status=s.status,
        start_date=s.start_date,
        expiry_date=s.expiry_date,
        payment_terms=s.payment_terms,
        quotation_valid_until=s.quotation_valid_until,
        next_invoice_date=s.next_invoice_date,
        lines=lines,
        discount_ids=[str(d) for d in s.discount_ids],
        status_history=history,
        created_at=s.created_at,
        updated_at=s.updated_at
    )

@router.get("", response_model=PaginatedResponse[SubscriptionResponse])
async def list_subscriptions(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin", "staff"))
):
    items, total = await SubscriptionService.list_subscriptions(
        customer_id_filter=customer_id,
        status_filter=status,
        q=q,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse(
        items=[to_subscription_response(s) for s in items],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{id}", response_model=SubscriptionResponse)
async def get_subscription(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    sub = await SubscriptionService.get_subscription(id)
    return to_subscription_response(sub)

@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    req: SubscriptionCreate,
    current_user: User = Depends(require_role("admin", "staff"))
):
    sub = await SubscriptionService.create_subscription(req, actor=current_user.email)
    return to_subscription_response(sub)

@router.put("/{id}", response_model=SubscriptionResponse)
async def update_subscription(
    id: str,
    req: SubscriptionUpdate,
    current_user: User = Depends(require_role("admin", "staff"))
):
    sub = await SubscriptionService.update_subscription(id, req, actor=current_user.email)
    return to_subscription_response(sub)

@router.post("/{id}/transition", response_model=SubscriptionResponse)
async def transition_subscription(
    id: str,
    req: SubscriptionTransitionRequest,
    current_user: User = Depends(require_role("admin", "staff"))
):
    sub = await SubscriptionService.transition_subscription(id, req.to, actor=current_user.email)
    return to_subscription_response(sub)

@router.post("/{id}/renew", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def renew_subscription(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    sub = await SubscriptionService.renew_subscription(id, actor=current_user.email)
    return to_subscription_response(sub)
