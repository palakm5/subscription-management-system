from datetime import datetime, date, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from beanie import PydanticObjectId

from app.core.errors import EntityNotFound, BusinessRuleViolation
from app.core.money import sub_money, ZERO
from app.models.invoices import Invoice, InvoiceStatus
from app.state.invoice_fsm import validate_invoice_transition
from app.services.pdf_service import generate_invoice_pdf

class InvoiceService:
    @staticmethod
    async def list_invoices(
        status_filter: Optional[str] = None,
        overdue_filter: Optional[bool] = None,
        customer_id_filter: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
        scoped_customer_id: Optional[PydanticObjectId] = None
    ) -> Tuple[List[Invoice], int]:
        query: Dict[str, Any] = {}

        # Row-level customer scoping
        effective_cust_id = scoped_customer_id or (PydanticObjectId(customer_id_filter) if customer_id_filter else None)
        if effective_cust_id:
            query["customer_id"] = effective_cust_id

        today = date.today()
        today_dt = datetime.combine(today, datetime.min.time())

        if overdue_filter is True:
            # Overdue is derived, never stored:
            # status == confirmed AND due_date < today AND amount_paid < total
            query["status"] = InvoiceStatus.CONFIRMED.value
            query["$or"] = [
                {"due_date": {"$lt": today_dt}},
                {"due_date": {"$lt": str(today)}}
            ]
            query["$expr"] = {"$lt": ["$amount_paid", "$total"]}
        elif status_filter:
            query["status"] = status_filter

        if from_date or to_date:
            date_q = {}
            if from_date:
                date_q["$gte"] = datetime.combine(from_date, datetime.min.time())
            if to_date:
                date_q["$lte"] = datetime.combine(to_date, datetime.max.time())
            query["issue_date"] = date_q

        total = await Invoice.find(query).count()
        skip = (page - 1) * page_size
        items = await Invoice.find(query).sort("-created_at").skip(skip).limit(page_size).to_list()
        return items, total

    @staticmethod
    async def get_invoice(invoice_id: str, scoped_customer_id: Optional[PydanticObjectId] = None) -> Invoice:
        query = {"_id": PydanticObjectId(invoice_id)}
        if scoped_customer_id:
            query["customer_id"] = scoped_customer_id

        inv = await Invoice.find_one(query)
        if not inv:
            raise EntityNotFound(f"Invoice with id '{invoice_id}' not found.")
        return inv

    @staticmethod
    async def confirm_invoice(invoice_id: str) -> Invoice:
        inv = await InvoiceService.get_invoice(invoice_id)
        validate_invoice_transition(inv.status.value, "confirmed")
        inv.status = InvoiceStatus.CONFIRMED
        inv.updated_at = datetime.now(timezone.utc)
        await inv.save()
        return inv

    @staticmethod
    async def cancel_invoice(invoice_id: str) -> Invoice:
        inv = await InvoiceService.get_invoice(invoice_id)
        validate_invoice_transition(inv.status.value, "cancelled")
        inv.status = InvoiceStatus.CANCELLED
        inv.updated_at = datetime.now(timezone.utc)
        await inv.save()
        return inv

    @staticmethod
    async def send_invoice(invoice_id: str) -> Invoice:
        inv = await InvoiceService.get_invoice(invoice_id)
        inv.sent_at = datetime.now(timezone.utc)
        inv.updated_at = datetime.now(timezone.utc)
        await inv.save()
        return inv

    @staticmethod
    async def get_invoice_pdf(invoice_id: str, scoped_customer_id: Optional[PydanticObjectId] = None) -> Tuple[bytes, str]:
        inv = await InvoiceService.get_invoice(invoice_id, scoped_customer_id)
        pdf_data = generate_invoice_pdf(inv)
        filename = f"invoice-{inv.number}.pdf"
        return pdf_data, filename
