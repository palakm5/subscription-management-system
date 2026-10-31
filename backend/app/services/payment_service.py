from datetime import datetime, date, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from bson import Decimal128
from beanie import PydanticObjectId

from app.core.db import get_client
from app.core.config import settings
from app.core.money import quantize_money, add_money, sub_money, ZERO
from app.core.errors import EntityNotFound, BusinessRuleViolation
from app.models.invoices import Invoice, InvoiceStatus
from app.models.payments import Payment, PaymentMethod
from app.schemas.payments import PaymentCreate

class PaymentService:
    @staticmethod
    async def record_payment(
        invoice_id: str,
        req: PaymentCreate,
        actor: str,
        scoped_customer_id: Optional[PydanticObjectId] = None
    ) -> Tuple[Payment, Invoice]:
        client = get_client()
        db = client[settings.DATABASE_NAME]
        inv_oid = PydanticObjectId(invoice_id)

        # 1. Fetch and validate invoice
        query = {"_id": inv_oid}
        if scoped_customer_id:
            query["customer_id"] = scoped_customer_id
        
        invoice = await Invoice.find_one(query)
        if not invoice:
            raise EntityNotFound(f"Invoice '{invoice_id}' not found.")

        # Business rule: Payments can only be recorded against confirmed invoices
        if invoice.status != InvoiceStatus.CONFIRMED:
            raise BusinessRuleViolation(
                f"Payments can only be recorded on 'confirmed' invoices. Current invoice status is '{invoice.status.value}'."
            )

        pay_amount = quantize_money(req.amount)
        if pay_amount <= ZERO:
            raise BusinessRuleViolation("Payment amount must be greater than zero.")

        balance_due = sub_money(invoice.total, invoice.amount_paid)
        if pay_amount > balance_due:
            raise BusinessRuleViolation(
                f"Overpayment rejected. Payment amount (${pay_amount:.2f}) exceeds outstanding balance (${balance_due:.2f})."
            )

        payment_date = req.paid_on or date.today()
        new_amount_paid = add_money(invoice.amount_paid, pay_amount)
        is_fully_paid = new_amount_paid >= invoice.total
        new_status = InvoiceStatus.PAID.value if is_fully_paid else InvoiceStatus.CONFIRMED.value

        payment = Payment(
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
            method=req.method,
            amount=pay_amount,
            paid_on=payment_date,
            note=req.note,
            recorded_by=actor
        )

        # 2. Execute atomically in MongoDB transaction
        async with await client.start_session() as session:
            async with session.start_transaction():
                # Insert payment document
                await payment.insert(session=session)

                # Atomically increment amount_paid and update status if fully paid
                await db.invoices.update_one(
                    {"_id": inv_oid},
                    {
                        "$inc": {"amount_paid": Decimal128(pay_amount)},
                        "$set": {
                            "status": new_status,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    },
                    session=session
                )

        # Reload updated invoice
        updated_invoice = await Invoice.get(inv_oid)
        return payment, updated_invoice

    @staticmethod
    async def list_payments(
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        method: Optional[PaymentMethod] = None,
        page: int = 1,
        page_size: int = 20,
        scoped_customer_id: Optional[PydanticObjectId] = None
    ) -> Tuple[List[Payment], int]:
        query = {}
        if scoped_customer_id:
            query["customer_id"] = scoped_customer_id
        if method:
            query["method"] = method.value
        if from_date or to_date:
            date_q = {}
            if from_date:
                date_q["$gte"] = from_date
            if to_date:
                date_q["$lte"] = to_date
            query["paid_on"] = date_q

        total = await Payment.find(query).count()
        skip = (page - 1) * page_size
        items = await Payment.find(query).sort("-paid_on").skip(skip).limit(page_size).to_list()
        return items, total
