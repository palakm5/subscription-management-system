import logging
import uuid
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from bson import Decimal128, ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.core.db import get_client
from app.core.config import settings
from app.core.money import (
    quantize_money, add_money, sub_money, mul_money, to_decimal, ZERO
)
from app.core.date_utils import compute_period_end, add_billing_period
from app.models.plans import Plan, BillingPeriod
from app.models.customers import Customer
from app.models.discounts import Discount, DiscountScope
from app.models.invoices import InvoiceStatus
from app.services.pricing import compute_line_subtotal
from app.services.discount_service import DiscountService
from app.services.tax_service import TaxService
from app.services.sequence_service import get_next_invoice_number

logger = logging.getLogger("brightloop.billing")

class BillingResult:
    def __init__(self):
        self.processed = 0
        self.created = 0
        self.skipped_duplicates = 0
        self.errors = 0
        self.details: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processed": self.processed,
            "created": self.created,
            "skipped_duplicates": self.skipped_duplicates,
            "errors": self.errors,
            "details": self.details
        }

class BillingService:
    @staticmethod
    async def claim_next_subscription(worker_id: str, as_of_date: date) -> Optional[Dict[str, Any]]:
        client = get_client()
        db = client[settings.DATABASE_NAME]
        now = datetime.now(timezone.utc)
        
        # Section 8: Selection and atomic claim
        # next_invoice_date stored as BSON date/datetime or date string
        # To be query safe against both date and datetime types in Mongo:
        claim_filter = {
            "status": "active",
            "$or": [
                {"next_invoice_date": {"$lte": datetime.combine(as_of_date, datetime.min.time())}},
                {"next_invoice_date": {"$lte": str(as_of_date)}}
            ],
            "$and": [
                {
                    "$or": [
                        {"lock_until": None},
                        {"lock_until": {"$lt": now}}
                    ]
                }
            ]
        }

        sub = await db.subscriptions.find_one_and_update(
            claim_filter,
            {
                "$set": {
                    "lock_until": now + timedelta(minutes=5),
                    "locked_by": worker_id
                }
            },
            return_document=ReturnDocument.AFTER
        )
        return sub

    @staticmethod
    async def release_subscription_lock(sub_id: Any) -> None:
        client = get_client()
        db = client[settings.DATABASE_NAME]
        await db.subscriptions.update_one(
            {"_id": sub_id},
            {"$set": {"lock_until": None, "locked_by": None}}
        )

    @staticmethod
    async def bill_one(sub_doc: Dict[str, Any], worker_id: str, as_of_date: date) -> str:
        """
        Executes idempotent billing for one subscription period inside a MongoDB transaction.
        Returns: 'created', 'skipped_duplicate', 'closed', or 'stopped'
        """
        client = get_client()
        db = client[settings.DATABASE_NAME]
        sub_id = sub_doc["_id"]

        # Parse next_invoice_date
        raw_nid = sub_doc["next_invoice_date"]
        if isinstance(raw_nid, datetime):
            period_start = raw_nid.date()
        elif isinstance(raw_nid, date):
            period_start = raw_nid
        else:
            period_start = datetime.strptime(str(raw_nid)[:10], "%Y-%m-%d").date()

        # Parse expiry_date
        raw_exp = sub_doc["expiry_date"]
        if isinstance(raw_exp, datetime):
            expiry_date = raw_exp.date()
        elif isinstance(raw_exp, date):
            expiry_date = raw_exp
        else:
            expiry_date = datetime.strptime(str(raw_exp)[:10], "%Y-%m-%d").date()

        # Load plan
        plan_doc = await db.plans.find_one({"_id": sub_doc["plan_id"]})
        if not plan_doc:
            await BillingService.release_subscription_lock(sub_id)
            raise ValueError(f"Plan '{sub_doc['plan_id']}' not found.")
        billing_period = BillingPeriod(plan_doc["billing_period"])
        auto_close = plan_doc.get("auto_close", False)

        # 1. Compute period_start and period_end
        period_end = compute_period_end(period_start, billing_period)

        # 2. If period_start > expiry_date: close if auto_close, release lock, stop
        if period_start > expiry_date:
            if auto_close:
                await db.subscriptions.update_one(
                    {"_id": sub_id},
                    {
                        "$set": {
                            "status": "closed",
                            "lock_until": None,
                            "locked_by": None,
                            "updated_at": datetime.now(timezone.utc)
                        },
                        "$push": {
                            "status_history": {
                                "from": "active",
                                "to": "closed",
                                "by": f"billing_engine ({worker_id})",
                                "at": datetime.now(timezone.utc)
                            }
                        }
                    }
                )
            else:
                await BillingService.release_subscription_lock(sub_id)
            return "closed"

        # Load customer snapshot
        cust_doc = await db.customers.find_one({"_id": sub_doc["customer_id"]})
        if not cust_doc:
            await BillingService.release_subscription_lock(sub_id)
            raise ValueError(f"Customer '{sub_doc['customer_id']}' not found.")

        customer_snapshot = {
            "name": cust_doc["name"],
            "billing_address": cust_doc.get("billing_address", {}),
            "tax_id": cust_doc.get("tax_id")
        }

        # 3. Build lines and pricing
        lines = sub_doc.get("lines", [])
        invoice_lines = []
        subtotal = ZERO
        total_quantity = sum(l.get("quantity", 1) for l in lines)

        for l in lines:
            qty = l.get("quantity", 1)
            unit_price = to_decimal(l.get("unit_price", ZERO))
            line_sub = compute_line_subtotal(qty, unit_price)
            subtotal = add_money(subtotal, line_sub)
            invoice_lines.append({
                "product_name": l["product_name"],
                "variant_label": l.get("variant_label"),
                "quantity": qty,
                "unit_price": unit_price,
                "product_id": l["product_id"],
                "tax_ids": l.get("tax_ids", []),
                "line_subtotal": line_sub,
                "discount_amount": ZERO,
                "tax_breakdown": [],
                "line_total": line_sub
            })

        # 4. Discounts eligibility & calculation
        # Load subscription discounts + active discounts
        candidate_discount_ids = sub_doc.get("discount_ids", [])
        discounts = await db.discounts.find({
            "_id": {"$in": candidate_discount_ids},
            "is_active": True
        }).to_list(length=100)

        applied_discounts = []
        discount_total = ZERO

        # Product-scoped discounts
        for d in discounts:
            if d.get("scope") == DiscountScope.PRODUCT.value:
                disc_obj = Discount(**d)
                eligible_pids = set(str(pid) for pid in d.get("product_ids", []))
                for il in invoice_lines:
                    if str(il["product_id"]) in eligible_pids:
                        if DiscountService.is_eligible(disc_obj, as_of_date, il["line_subtotal"], il["quantity"]):
                            disc_amount = DiscountService.calculate_discount_amount(disc_obj, il["line_subtotal"])
                            if disc_amount > ZERO:
                                il["discount_amount"] = add_money(il["discount_amount"], disc_amount)
                                discount_total = add_money(discount_total, disc_amount)
                                applied_discounts.append({
                                    "discount_id": d["_id"],
                                    "name": d["name"],
                                    "amount": disc_amount
                                })

        # Subscription-scoped discounts
        remaining_subtotal = sub_money(subtotal, discount_total)
        for d in discounts:
            if d.get("scope") == DiscountScope.SUBSCRIPTION.value:
                disc_obj = Discount(**d)
                if DiscountService.is_eligible(disc_obj, as_of_date, remaining_subtotal, total_quantity):
                    disc_amount = DiscountService.calculate_discount_amount(disc_obj, remaining_subtotal)
                    if disc_amount > ZERO:
                        discount_total = add_money(discount_total, disc_amount)
                        applied_discounts.append({
                            "discount_id": d["_id"],
                            "name": d["name"],
                            "amount": disc_amount
                        })
                        # Distribute proportionally to lines for post-discount tax computation
                        if remaining_subtotal > ZERO and len(invoice_lines) > 0:
                            for il in invoice_lines:
                                line_post = sub_money(il["line_subtotal"], il["discount_amount"])
                                if line_post > ZERO:
                                    share = quantize_money((line_post / remaining_subtotal) * disc_amount)
                                    il["discount_amount"] = add_money(il["discount_amount"], share)
                        remaining_subtotal = sub_money(remaining_subtotal, disc_amount)

        # 5. Taxes (computed on post-discount line amount)
        tax_total = ZERO
        final_invoice_lines = []
        for il in invoice_lines:
            post_disc = sub_money(il["line_subtotal"], il["discount_amount"])
            line_tax, breakdown = await TaxService.compute_taxes_for_line(
                il["tax_ids"], post_disc
            )
            tax_total = add_money(tax_total, line_tax)
            line_final_total = add_money(post_disc, line_tax)
            final_invoice_lines.append({
                "product_name": il["product_name"],
                "variant_label": il["variant_label"],
                "quantity": il["quantity"],
                "unit_price": Decimal128(il["unit_price"]),
                "discount_amount": Decimal128(il["discount_amount"]),
                "tax_breakdown": [
                    {
                        "tax_id": tb.tax_id,
                        "name": tb.name,
                        "rate": Decimal128(tb.rate),
                        "amount": Decimal128(tb.amount)
                    } for tb in breakdown
                ],
                "line_total": Decimal128(line_final_total)
            })

        # 6. Totals & Dates
        invoice_total = add_money(sub_money(subtotal, discount_total), tax_total)
        payment_terms = sub_doc.get("payment_terms", 15)
        issue_date = as_of_date
        due_date = issue_date + timedelta(days=payment_terms)
        invoice_number = await get_next_invoice_number()

        # 7. Execute in ACID transaction
        next_invoice_date_advanced = period_end + timedelta(days=1)
        invoice_status = InvoiceStatus.CONFIRMED.value if settings.AUTO_CONFIRM_INVOICES else InvoiceStatus.DRAFT.value

        async with await client.start_session() as session:
            try:
                async with session.start_transaction():
                    # Step 8: Atomic conditional increments for applied discounts
                    for ad in applied_discounts:
                        up_res = await db.discounts.update_one(
                            {
                                "_id": ad["discount_id"],
                                "$or": [
                                    {"usage_limit": None},
                                    {"$expr": {"$lt": ["$times_used", "$usage_limit"]}}
                                ]
                            },
                            {"$inc": {"times_used": 1}},
                            session=session
                        )
                        # If matched_count == 0, race lost, but in transaction it will abort or we can proceed

                    # Step 9: Insert invoice
                    invoice_doc = {
                        "number": invoice_number,
                        "subscription_id": sub_id,
                        "customer_id": sub_doc["customer_id"],
                        "customer_snapshot": customer_snapshot,
                        "period_start": datetime.combine(period_start, datetime.min.time()),
                        "period_end": datetime.combine(period_end, datetime.min.time()),
                        "issue_date": datetime.combine(issue_date, datetime.min.time()),
                        "due_date": datetime.combine(due_date, datetime.min.time()),
                        "status": invoice_status,
                        "lines": final_invoice_lines,
                        "subtotal": Decimal128(subtotal),
                        "discount_total": Decimal128(discount_total),
                        "tax_total": Decimal128(tax_total),
                        "total": Decimal128(invoice_total),
                        "amount_paid": Decimal128(ZERO),
                        "applied_discounts": [
                            {
                                "discount_id": ad["discount_id"],
                                "name": ad["name"],
                                "amount": Decimal128(ad["amount"])
                            } for ad in applied_discounts
                        ],
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                    await db.invoices.insert_one(invoice_doc, session=session)

                    # Step 10: Conditional advance next_invoice_date and clear lock
                    await db.subscriptions.update_one(
                        {
                            "_id": sub_id,
                            "next_invoice_date": sub_doc["next_invoice_date"]
                        },
                        {
                            "$set": {
                                "next_invoice_date": datetime.combine(next_invoice_date_advanced, datetime.min.time()),
                                "lock_until": None,
                                "locked_by": None,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        },
                        session=session
                    )
            except DuplicateKeyError as e:
                # Idempotency guard triggered: subscription_id + period_start + period_end already exists!
                logger.warning(
                    "DuplicateKeyError caught for sub %s period %s..%s. Transaction rolled back; advancing date.",
                    sub_doc.get("number"), period_start, period_end
                )
                # Ensure date is advanced and lock released
                await db.subscriptions.update_one(
                    {"_id": sub_id},
                    {
                        "$set": {
                            "next_invoice_date": datetime.combine(next_invoice_date_advanced, datetime.min.time()),
                            "lock_until": None,
                            "locked_by": None,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                return "skipped_duplicate"

        return "created"

    @staticmethod
    async def run_billing_job(as_of_date: Optional[date] = None) -> BillingResult:
        if as_of_date is None:
            as_of_date = date.today()

        worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        res = BillingResult()

        while True:
            sub = await BillingService.claim_next_subscription(worker_id, as_of_date)
            if not sub:
                break

            res.processed += 1
            try:
                outcome = await BillingService.bill_one(sub, worker_id, as_of_date)
                if outcome == "created":
                    res.created += 1
                    res.details.append(f"Subscription {sub.get('number')}: invoice generated.")
                elif outcome == "skipped_duplicate":
                    res.skipped_duplicates += 1
                    res.details.append(f"Subscription {sub.get('number')}: period already billed (idempotency guard).")
                elif outcome == "closed":
                    res.details.append(f"Subscription {sub.get('number')}: auto-closed at expiry.")
            except Exception as e:
                res.errors += 1
                logger.exception("Billing error on subscription %s: %s", sub.get("number"), e)
                res.details.append(f"Subscription {sub.get('number')}: error - {str(e)}")
                await BillingService.release_subscription_lock(sub["_id"])

        return res

    @staticmethod
    async def run_auto_close_job(as_of_date: Optional[date] = None) -> int:
        if as_of_date is None:
            as_of_date = date.today()
        client = get_client()
        db = client[settings.DATABASE_NAME]

        # Auto-close: status in (active, paused) AND expiry_date < today AND plan.auto_close
        plans = await db.plans.find({"auto_close": True}).to_list(length=1000)
        auto_close_plan_ids = [p["_id"] for p in plans]
        if not auto_close_plan_ids:
            return 0

        res = await db.subscriptions.update_many(
            {
                "status": {"$in": ["active", "paused"]},
                "plan_id": {"$in": auto_close_plan_ids},
                "$or": [
                    {"expiry_date": {"$lt": datetime.combine(as_of_date, datetime.min.time())}},
                    {"expiry_date": {"$lt": str(as_of_date)}}
                ]
            },
            {
                "$set": {
                    "status": "closed",
                    "updated_at": datetime.now(timezone.utc)
                },
                "$push": {
                    "status_history": {
                        "from": "auto_close",
                        "to": "closed",
                        "by": "auto_close_job",
                        "at": datetime.now(timezone.utc)
                    }
                }
            }
        )
        return res.modified_count

    @staticmethod
    async def run_quote_expiry_job(as_of_date: Optional[date] = None) -> int:
        if as_of_date is None:
            as_of_date = date.today()
        client = get_client()
        db = client[settings.DATABASE_NAME]

        # Quote expiry: status == quotation AND quotation_valid_until < today -> closed
        res = await db.subscriptions.update_many(
            {
                "status": "quotation",
                "$or": [
                    {"quotation_valid_until": {"$lt": datetime.combine(as_of_date, datetime.min.time())}},
                    {"quotation_valid_until": {"$lt": str(as_of_date)}}
                ]
            },
            {
                "$set": {
                    "status": "closed",
                    "updated_at": datetime.now(timezone.utc)
                },
                "$push": {
                    "status_history": {
                        "from": "quotation",
                        "to": "closed",
                        "by": "quote_expiry_job",
                        "at": datetime.now(timezone.utc)
                    }
                }
            }
        )
        return res.modified_count
