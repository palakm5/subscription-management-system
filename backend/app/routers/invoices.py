from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
import io

from app.core.deps import require_role
from app.core.pagination import PaginatedResponse
from app.core.money import sub_money
from app.models.users import User
from app.models.invoices import Invoice
from app.schemas.invoices import (
    InvoiceResponse, InvoiceLineOut, TaxBreakdownItemOut, AppliedDiscountOut
)
from app.schemas.payments import PaymentCreate, PaymentResponse
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/invoices", tags=["invoices"])

def to_invoice_response(inv: Invoice) -> InvoiceResponse:
    lines = [
        InvoiceLineOut(
            product_name=l.product_name,
            variant_label=l.variant_label,
            quantity=l.quantity,
            unit_price=l.unit_price,
            discount_amount=l.discount_amount,
            tax_breakdown=[
                TaxBreakdownItemOut(
                    tax_id=str(tb.tax_id),
                    name=tb.name,
                    rate=tb.rate,
                    amount=tb.amount
                ) for tb in l.tax_breakdown
            ],
            line_total=l.line_total
        ) for l in inv.lines
    ]
    discounts = [
        AppliedDiscountOut(
            discount_id=str(ad.discount_id),
            name=ad.name,
            amount=ad.amount
        ) for ad in inv.applied_discounts
    ]
    balance = sub_money(inv.total, inv.amount_paid)
    return InvoiceResponse(
        id=str(inv.id),
        number=inv.number,
        subscription_id=str(inv.subscription_id),
        customer_id=str(inv.customer_id),
        customer_snapshot=inv.customer_snapshot,
        period_start=inv.period_start,
        period_end=inv.period_end,
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        status=inv.status,
        is_overdue=inv.is_overdue,
        lines=lines,
        subtotal=inv.subtotal,
        discount_total=inv.discount_total,
        tax_total=inv.tax_total,
        total=inv.total,
        amount_paid=inv.amount_paid,
        balance_due=balance,
        applied_discounts=discounts,
        sent_at=inv.sent_at,
        created_at=inv.created_at,
        updated_at=inv.updated_at
    )

@router.get("", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    status: Optional[str] = None,
    overdue: Optional[bool] = None,
    customer_id: Optional[str] = None,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin", "staff"))
):
    invoices, total = await InvoiceService.list_invoices(
        status_filter=status,
        overdue_filter=overdue,
        customer_id_filter=customer_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse(
        items=[to_invoice_response(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{id}", response_model=InvoiceResponse)
async def get_invoice(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    inv = await InvoiceService.get_invoice(id)
    return to_invoice_response(inv)

@router.post("/{id}/confirm", response_model=InvoiceResponse)
async def confirm_invoice(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    inv = await InvoiceService.confirm_invoice(id)
    return to_invoice_response(inv)

@router.post("/{id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    inv = await InvoiceService.cancel_invoice(id)
    return to_invoice_response(inv)

@router.post("/{id}/send", response_model=InvoiceResponse)
async def send_invoice(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    inv = await InvoiceService.send_invoice(id)
    return to_invoice_response(inv)

@router.get("/{id}/pdf")
async def get_invoice_pdf(
    id: str,
    current_user: User = Depends(require_role("admin", "staff"))
):
    pdf_bytes, filename = await InvoiceService.get_invoice_pdf(id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )

@router.post("/{id}/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment_for_invoice(
    id: str,
    req: PaymentCreate,
    current_user: User = Depends(require_role("admin", "staff"))
):
    payment, _ = await PaymentService.record_payment(id, req, actor=current_user.email)
    return PaymentResponse(
        id=str(payment.id),
        invoice_id=str(payment.invoice_id),
        customer_id=str(payment.customer_id),
        method=payment.method,
        amount=payment.amount,
        paid_on=payment.paid_on,
        note=payment.note,
        recorded_by=payment.recorded_by,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )
