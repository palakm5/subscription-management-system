from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status

from app.core.deps import current_customer_scope, get_current_user, CustomerScope
from app.core.pagination import PaginatedResponse
from app.models.users import User
from app.models.customers import Customer
from app.schemas.subscriptions import (
    SubscriptionResponse, SubscriptionTransitionRequest
)
from app.schemas.invoices import InvoiceResponse
from app.schemas.catalog import CustomerResponse, CustomerUpdate
from app.services.subscription_service import SubscriptionService
from app.services.invoice_service import InvoiceService
from app.services.catalog_service import CatalogService
from app.routers.subscriptions import to_subscription_response
from app.routers.invoices import to_invoice_response
from app.routers.customers import to_customer_response

router = APIRouter(prefix="/portal", tags=["portal"])

@router.get("/subscriptions", response_model=PaginatedResponse[SubscriptionResponse])
async def list_portal_subscriptions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    scope: CustomerScope = Depends(current_customer_scope)
):
    items, total = await SubscriptionService.list_subscriptions(
        customer_id_filter=str(scope.customer_id),
        page=page,
        page_size=page_size
    )
    return PaginatedResponse(
        items=[to_subscription_response(s) for s in items],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/subscriptions/{id}", response_model=SubscriptionResponse)
async def get_portal_subscription(
    id: str,
    scope: CustomerScope = Depends(current_customer_scope)
):
    sub = await SubscriptionService.get_subscription(id, scoped_customer_id=scope.customer_id)
    return to_subscription_response(sub)

@router.post("/subscriptions/{id}/transition", response_model=SubscriptionResponse)
async def transition_portal_subscription(
    id: str,
    req: SubscriptionTransitionRequest,
    current_user: User = Depends(get_current_user),
    scope: CustomerScope = Depends(current_customer_scope)
):
    # Customer can pause/close if plan permits
    sub = await SubscriptionService.transition_subscription(
        id, req.to, actor=current_user.email, scoped_customer_id=scope.customer_id
    )
    return to_subscription_response(sub)

@router.get("/invoices", response_model=PaginatedResponse[InvoiceResponse])
async def list_portal_invoices(
    status: Optional[str] = None,
    overdue: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    scope: CustomerScope = Depends(current_customer_scope)
):
    invoices, total = await InvoiceService.list_invoices(
        status_filter=status,
        overdue_filter=overdue,
        page=page,
        page_size=page_size,
        scoped_customer_id=scope.customer_id
    )
    return PaginatedResponse(
        items=[to_invoice_response(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/invoices/{id}", response_model=InvoiceResponse)
async def get_portal_invoice(
    id: str,
    scope: CustomerScope = Depends(current_customer_scope)
):
    inv = await InvoiceService.get_invoice(id, scoped_customer_id=scope.customer_id)
    return to_invoice_response(inv)

@router.get("/invoices/{id}/pdf")
async def get_portal_invoice_pdf(
    id: str,
    scope: CustomerScope = Depends(current_customer_scope)
):
    pdf_bytes, filename = await InvoiceService.get_invoice_pdf(id, scoped_customer_id=scope.customer_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )

@router.get("/profile", response_model=CustomerResponse)
async def get_portal_profile(
    scope: CustomerScope = Depends(current_customer_scope)
):
    cust = await CatalogService.get_customer(str(scope.customer_id))
    return to_customer_response(cust)

@router.put("/profile", response_model=CustomerResponse)
async def update_portal_profile(
    req: CustomerUpdate,
    scope: CustomerScope = Depends(current_customer_scope)
):
    cust = await CatalogService.update_customer(str(scope.customer_id), req)
    return to_customer_response(cust)
