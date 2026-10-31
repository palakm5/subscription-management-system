from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.deps import require_role
from app.core.pagination import PaginatedResponse
from app.models.users import User
from app.models.payments import Payment, PaymentMethod
from app.schemas.payments import PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])

def to_payment_response(p: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=str(p.id),
        invoice_id=str(p.invoice_id),
        customer_id=str(p.customer_id),
        method=p.method,
        amount=p.amount,
        paid_on=p.paid_on,
        note=p.note,
        recorded_by=p.recorded_by,
        created_at=p.created_at,
        updated_at=p.updated_at
    )

@router.get("", response_model=PaginatedResponse[PaymentResponse])
async def list_payments(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    method: Optional[PaymentMethod] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin", "staff"))
):
    payments, total = await PaymentService.list_payments(
        from_date=from_date,
        to_date=to_date,
        method=method,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse(
        items=[to_payment_response(p) for p in payments],
        total=total,
        page=page,
        page_size=page_size
    )
