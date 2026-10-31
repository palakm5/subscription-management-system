from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from bson import ObjectId
from beanie import PydanticObjectId
from dateutil.relativedelta import relativedelta

from app.core.money import quantize_money, add_money, mul_money
from app.core.errors import EntityNotFound, BusinessRuleViolation
from app.core.date_utils import add_billing_period, compute_period_end
from app.models.subscriptions import (
    Subscription, SubscriptionLine, StatusHistoryEntry, SubscriptionStatus
)
from app.models.plans import Plan, BillingPeriod
from app.models.products import Product
from app.models.customers import Customer
from app.models.quotation_templates import QuotationTemplate
from app.state.subscription_fsm import validate_subscription_transition
from app.services.sequence_service import get_next_subscription_number
from app.schemas.subscriptions import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionLineIn
)

class SubscriptionService:
    @staticmethod
    async def build_lines(lines_in: List[SubscriptionLineIn], plan: Plan) -> List[SubscriptionLine]:
        built_lines: List[SubscriptionLine] = []
        for l in lines_in:
            if l.quantity < plan.min_quantity:
                raise BusinessRuleViolation(
                    f"Line quantity ({l.quantity}) must be greater than or equal to plan minimum quantity ({plan.min_quantity})."
                )

            prod = await Product.get(PydanticObjectId(l.product_id))
            if not prod:
                raise EntityNotFound(f"Product '{l.product_id}' not found.")

            variant_label = None
            extra_price = Decimal("0.00")
            if l.variant_id:
                var = next((v for v in prod.variants if v.id == l.variant_id), None)
                if not var:
                    raise EntityNotFound(f"Variant '{l.variant_id}' not found on product '{prod.name}'.")
                variant_label = f"{var.attribute}: {var.value}"
                extra_price = var.extra_price

            unit_price = l.unit_price
            if unit_price is None:
                # Rule: Final unit price = product sales_price + variant extra_price
                unit_price = add_money(prod.sales_price, extra_price)
            else:
                unit_price = quantize_money(unit_price)

            amount = mul_money(unit_price, l.quantity)

            built_lines.append(SubscriptionLine(
                line_id=str(ObjectId()),
                product_id=prod.id,
                product_name=prod.name,
                variant_id=l.variant_id,
                variant_label=variant_label,
                quantity=l.quantity,
                unit_price=unit_price,
                tax_ids=prod.tax_ids,
                amount=amount
            ))
        return built_lines

    @staticmethod
    async def create_subscription(req: SubscriptionCreate, actor: str) -> Subscription:
        # Validate customer
        cust = await Customer.get(PydanticObjectId(req.customer_id))
        if not cust:
            raise EntityNotFound(f"Customer with id '{req.customer_id}' not found.")

        template: Optional[QuotationTemplate] = None
        plan_id = req.plan_id

        if req.template_id:
            template = await QuotationTemplate.get(PydanticObjectId(req.template_id))
            if not template:
                raise EntityNotFound(f"Quotation template '{req.template_id}' not found.")
            if not plan_id:
                plan_id = str(template.plan_id)

        if not plan_id:
            raise BusinessRuleViolation("Plan ID is required to create a subscription.")

        plan = await Plan.get(PydanticObjectId(plan_id))
        if not plan:
            raise EntityNotFound(f"Plan with id '{plan_id}' not found.")

        today = date.today()
        start_date = req.start_date or today
        # Expiry default: 1 year from start date if not provided
        expiry_date = req.expiry_date or add_billing_period(start_date, plan.billing_period, count=12 if plan.billing_period == BillingPeriod.MONTHLY else 1)

        quotation_valid_until = None
        status = SubscriptionStatus.DRAFT

        # Determine lines
        lines_input: List[SubscriptionLineIn] = []
        if req.lines and len(req.lines) > 0:
            lines_input = req.lines
        elif template and template.lines:
            lines_input = [
                SubscriptionLineIn(
                    product_id=str(tl.product_id),
                    variant_id=tl.variant_id,
                    quantity=tl.quantity
                ) for tl in template.lines
            ]

        # Template quotation flow: valid_until = today + validity_days
        if template:
            quotation_valid_until = today + timedelta(days=template.validity_days)
            status = SubscriptionStatus.QUOTATION

        lines = await SubscriptionService.build_lines(lines_input, plan)
        sub_number = await get_next_subscription_number()

        sub = Subscription(
            number=sub_number,
            customer_id=cust.id,
            plan_id=plan.id,
            template_id=template.id if template else None,
            status=status,
            start_date=start_date,
            expiry_date=expiry_date,
            payment_terms=req.payment_terms,
            quotation_valid_until=quotation_valid_until,
            next_invoice_date=None,
            lines=lines,
            discount_ids=[PydanticObjectId(did) for did in req.discount_ids],
            status_history=[
                StatusHistoryEntry(
                    from_status=None,
                    to_status=status.value,
                    by=actor,
                    at=datetime.now(timezone.utc)
                )
            ]
        )
        await sub.insert()
        return sub

    @staticmethod
    async def list_subscriptions(
        customer_id_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Subscription], int]:
        query = {}
        if customer_id_filter:
            query["customer_id"] = PydanticObjectId(customer_id_filter)
        if status_filter:
            query["status"] = status_filter
        if q:
            query["number"] = {"$regex": q, "$options": "i"}

        total = await Subscription.find(query).count()
        skip = (page - 1) * page_size
        items = await Subscription.find(query).sort("-created_at").skip(skip).limit(page_size).to_list()
        return items, total

    @staticmethod
    async def get_subscription(subscription_id: str, scoped_customer_id: Optional[PydanticObjectId] = None) -> Subscription:
        query = {"_id": PydanticObjectId(subscription_id)}
        if scoped_customer_id:
            query["customer_id"] = scoped_customer_id

        sub = await Subscription.find_one(query)
        if not sub:
            # Row-level rule: returning another customer's record yields 404, not 403
            raise EntityNotFound(f"Subscription with id '{subscription_id}' not found.")
        return sub

    @staticmethod
    async def update_subscription(
        subscription_id: str,
        req: SubscriptionUpdate,
        actor: str,
        scoped_customer_id: Optional[PydanticObjectId] = None
    ) -> Subscription:
        sub = await SubscriptionService.get_subscription(subscription_id, scoped_customer_id)
        if sub.status not in (SubscriptionStatus.DRAFT, SubscriptionStatus.QUOTATION):
            raise BusinessRuleViolation(
                f"Subscriptions can only be edited while in 'draft' or 'quotation' status (current status: '{sub.status.value}')."
            )

        plan = await Plan.get(sub.plan_id)

        if req.start_date is not None:
            sub.start_date = req.start_date
        if req.expiry_date is not None:
            sub.expiry_date = req.expiry_date
        if req.payment_terms is not None:
            sub.payment_terms = req.payment_terms
        if req.quotation_valid_until is not None:
            sub.quotation_valid_until = req.quotation_valid_until
        if req.discount_ids is not None:
            sub.discount_ids = [PydanticObjectId(did) for did in req.discount_ids]
        if req.lines is not None:
            sub.lines = await SubscriptionService.build_lines(req.lines, plan)

        sub.updated_at = datetime.now(timezone.utc)
        await sub.save()
        return sub

    @staticmethod
    async def transition_subscription(
        subscription_id: str,
        target_status: str,
        actor: str,
        scoped_customer_id: Optional[PydanticObjectId] = None
    ) -> Subscription:
        sub = await SubscriptionService.get_subscription(subscription_id, scoped_customer_id)
        plan = await Plan.get(sub.plan_id)
        current_st = sub.status.value

        # FSM check + plan flags
        validate_subscription_transition(current_st, target_status, plan)

        today = date.today()
        # Side effects per spec
        if current_st == "confirmed" and target_status == "active":
            # On confirmed → active: set next_invoice_date = start_date
            sub.next_invoice_date = sub.start_date
        elif current_st == "paused" and target_status == "active":
            # On resume, do not back-bill the paused window (advance next_invoice_date to the next period boundary on or after today)
            next_date = sub.next_invoice_date or sub.start_date
            while next_date < today:
                next_date = add_billing_period(next_date, plan.billing_period, count=1)
            sub.next_invoice_date = next_date

        sub.status = SubscriptionStatus(target_status)
        sub.status_history.append(StatusHistoryEntry(
            from_status=current_st,
            to_status=target_status,
            by=actor,
            at=datetime.now(timezone.utc)
        ))
        sub.updated_at = datetime.now(timezone.utc)
        await sub.save()
        return sub

    @staticmethod
    async def renew_subscription(
        subscription_id: str,
        actor: str,
        scoped_customer_id: Optional[PydanticObjectId] = None
    ) -> Subscription:
        sub = await SubscriptionService.get_subscription(subscription_id, scoped_customer_id)
        plan = await Plan.get(sub.plan_id)
        if not plan.renewable:
            raise BusinessRuleViolation("This plan does not permit renewals.")

        # Renewal creates a NEW subscription with sequential number
        new_start = sub.expiry_date + timedelta(days=1)
        period_count = 12 if plan.billing_period == BillingPeriod.MONTHLY else 1
        new_expiry = add_billing_period(new_start, plan.billing_period, count=period_count)
        new_number = await get_next_subscription_number()

        new_sub = Subscription(
            number=new_number,
            customer_id=sub.customer_id,
            plan_id=sub.plan_id,
            template_id=sub.template_id,
            status=SubscriptionStatus.DRAFT,
            start_date=new_start,
            expiry_date=new_expiry,
            payment_terms=sub.payment_terms,
            lines=sub.lines,
            discount_ids=sub.discount_ids,
            status_history=[
                StatusHistoryEntry(
                    from_status=None,
                    to_status="draft",
                    by=f"{actor} (renewed from {sub.number})",
                    at=datetime.now(timezone.utc)
                )
            ]
        )
        await new_sub.insert()
        return new_sub
