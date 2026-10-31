from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.deps import require_role
from app.core.pagination import PaginatedResponse
from app.models.users import User
from app.schemas.reports import ReportSummaryResponse, RevenueReportResponse
from app.schemas.invoices import InvoiceResponse
from app.services.report_service import ReportService
from app.services.invoice_service import InvoiceService
from app.routers.invoices import to_invoice_response

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/summary", response_model=ReportSummaryResponse)
async def get_report_summary(
    current_user: User = Depends(require_role("admin", "staff"))
):
    return await ReportService.get_summary()

@router.get("/revenue", response_model=RevenueReportResponse)
async def get_revenue_report(
    group_by: str = Query(default="month"),
    current_user: User = Depends(require_role("admin", "staff"))
):
    return await ReportService.get_revenue_by_month()

@router.get("/overdue-invoices", response_model=PaginatedResponse[InvoiceResponse])
async def get_overdue_invoices_report(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("admin", "staff"))
):
    invoices, total = await InvoiceService.list_invoices(
        overdue_filter=True,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse(
        items=[to_invoice_response(inv) for inv in invoices],
        total=total,
        page=page,
        page_size=page_size
    )
