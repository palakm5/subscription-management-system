from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from bson import ObjectId
from beanie import PydanticObjectId

from app.core.money import quantize_money, add_money
from app.core.errors import EntityNotFound, BusinessRuleViolation
from app.models.products import Product, Variant
from app.models.plans import Plan
from app.models.taxes import Tax
from app.models.discounts import Discount, DiscountScope
from app.models.quotation_templates import QuotationTemplate, QuotationTemplateLine
from app.models.customers import Customer
from app.schemas.catalog import (
    ProductCreate, ProductUpdate, VariantIn,
    PlanCreate, PlanUpdate,
    TaxCreate, TaxUpdate,
    DiscountCreate, DiscountUpdate,
    QuotationTemplateCreate, QuotationTemplateUpdate,
    CustomerCreate, CustomerUpdate
)

class CatalogService:
    # ----------------- PRODUCTS -----------------
    @staticmethod
    async def list_products(is_active: Optional[bool] = None, q: Optional[str] = None) -> List[Product]:
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        if q:
            query["$text"] = {"$search": q}
        return await Product.find(query).sort("+name").to_list()

    @staticmethod
    async def get_product(product_id: str) -> Product:
        prod = await Product.get(PydanticObjectId(product_id))
        if not prod:
            raise EntityNotFound(f"Product with id '{product_id}' not found.")
        return prod

    @staticmethod
    async def create_product(req: ProductCreate) -> Product:
        variants = [
            Variant(
                id=str(ObjectId()),
                attribute=v.attribute.strip(),
                value=v.value.strip(),
                extra_price=quantize_money(v.extra_price)
            ) for v in req.variants
        ]
        prod = Product(
            name=req.name.strip(),
            type=req.type,
            sales_price=quantize_money(req.sales_price),
            cost_price=quantize_money(req.cost_price),
            notes=req.notes,
            tax_ids=[PydanticObjectId(t) for t in req.tax_ids],
            is_active=req.is_active,
            variants=variants
        )
        await prod.insert()
        return prod

    @staticmethod
    async def update_product(product_id: str, req: ProductUpdate) -> Product:
        prod = await CatalogService.get_product(product_id)
        if req.name is not None:
            prod.name = req.name.strip()
        if req.type is not None:
            prod.type = req.type
        if req.sales_price is not None:
            prod.sales_price = quantize_money(req.sales_price)
        if req.cost_price is not None:
            prod.cost_price = quantize_money(req.cost_price)
        if req.notes is not None:
            prod.notes = req.notes
        if req.tax_ids is not None:
            prod.tax_ids = [PydanticObjectId(t) for t in req.tax_ids]
        if req.is_active is not None:
            prod.is_active = req.is_active
        prod.updated_at = datetime.now(timezone.utc)
        await prod.save()
        return prod

    @staticmethod
    async def delete_product(product_id: str) -> None:
        prod = await CatalogService.get_product(product_id)
        await prod.delete()

    @staticmethod
    async def add_variant(product_id: str, req: VariantIn) -> Product:
        prod = await CatalogService.get_product(product_id)
        variant = Variant(
            id=str(ObjectId()),
            attribute=req.attribute.strip(),
            value=req.value.strip(),
            extra_price=quantize_money(req.extra_price)
        )
        prod.variants.append(variant)
        prod.updated_at = datetime.now(timezone.utc)
        await prod.save()
        return prod

    @staticmethod
    async def update_variant(product_id: str, variant_id: str, req: VariantIn) -> Product:
        prod = await CatalogService.get_product(product_id)
        found = False
        for v in prod.variants:
            if v.id == variant_id:
                v.attribute = req.attribute.strip()
                v.value = req.value.strip()
                v.extra_price = quantize_money(req.extra_price)
                found = True
                break
        if not found:
            raise EntityNotFound(f"Variant '{variant_id}' not found on product '{product_id}'.")
        prod.updated_at = datetime.now(timezone.utc)
        await prod.save()
        return prod

    @staticmethod
    async def delete_variant(product_id: str, variant_id: str) -> Product:
        prod = await CatalogService.get_product(product_id)
        initial_len = len(prod.variants)
        prod.variants = [v for v in prod.variants if v.id != variant_id]
        if len(prod.variants) == initial_len:
            raise EntityNotFound(f"Variant '{variant_id}' not found on product '{product_id}'.")
        prod.updated_at = datetime.now(timezone.utc)
        await prod.save()
        return prod

    # ----------------- PLANS -----------------
    @staticmethod
    async def list_plans(is_active: Optional[bool] = None) -> List[Plan]:
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        return await Plan.find(query).sort("+name").to_list()

    @staticmethod
    async def get_plan(plan_id: str) -> Plan:
        plan = await Plan.get(PydanticObjectId(plan_id))
        if not plan:
            raise EntityNotFound(f"Plan with id '{plan_id}' not found.")
        return plan

    @staticmethod
    async def create_plan(req: PlanCreate) -> Plan:
        plan = Plan(
            name=req.name.strip(),
            price=quantize_money(req.price),
            billing_period=req.billing_period,
            min_quantity=req.min_quantity,
            available_from=req.available_from,
            available_to=req.available_to,
            auto_close=req.auto_close,
            closable=req.closable,
            pausable=req.pausable,
            renewable=req.renewable,
            is_active=req.is_active
        )
        await plan.insert()
        return plan

    @staticmethod
    async def update_plan(plan_id: str, req: PlanUpdate) -> Plan:
        plan = await CatalogService.get_plan(plan_id)
        for field, value in req.model_dump(exclude_unset=True).items():
            if field == "price" and value is not None:
                value = quantize_money(value)
            setattr(plan, field, value)
        plan.updated_at = datetime.now(timezone.utc)
        await plan.save()
        return plan

    @staticmethod
    async def delete_plan(plan_id: str) -> None:
        plan = await CatalogService.get_plan(plan_id)
        await plan.delete()

    # ----------------- TAXES -----------------
    @staticmethod
    async def list_taxes(is_active: Optional[bool] = None) -> List[Tax]:
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        return await Tax.find(query).sort("+name").to_list()

    @staticmethod
    async def get_tax(tax_id: str) -> Tax:
        tax = await Tax.get(PydanticObjectId(tax_id))
        if not tax:
            raise EntityNotFound(f"Tax rule with id '{tax_id}' not found.")
        return tax

    @staticmethod
    async def create_tax(req: TaxCreate) -> Tax:
        tax = Tax(
            name=req.name.strip(),
            type=req.type,
            rate=quantize_money(req.rate),
            is_active=req.is_active
        )
        await tax.insert()
        return tax

    @staticmethod
    async def update_tax(tax_id: str, req: TaxUpdate) -> Tax:
        tax = await CatalogService.get_tax(tax_id)
        for field, value in req.model_dump(exclude_unset=True).items():
            if field == "rate" and value is not None:
                value = quantize_money(value)
            setattr(tax, field, value)
        tax.updated_at = datetime.now(timezone.utc)
        await tax.save()
        return tax

    @staticmethod
    async def delete_tax(tax_id: str) -> None:
        tax = await CatalogService.get_tax(tax_id)
        await tax.delete()

    # ----------------- DISCOUNTS -----------------
    @staticmethod
    async def list_discounts(is_active: Optional[bool] = None) -> List[Discount]:
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        return await Discount.find(query).sort("+name").to_list()

    @staticmethod
    async def get_discount(discount_id: str) -> Discount:
        disc = await Discount.get(PydanticObjectId(discount_id))
        if not disc:
            raise EntityNotFound(f"Discount with id '{discount_id}' not found.")
        return disc

    @staticmethod
    async def create_discount(req: DiscountCreate) -> Discount:
        if req.scope == DiscountScope.PRODUCT and not req.product_ids:
            raise BusinessRuleViolation("Product-scoped discount must specify at least one product ID.")
        
        disc = Discount(
            name=req.name.strip(),
            type=req.type,
            value=quantize_money(req.value),
            min_purchase=quantize_money(req.min_purchase) if req.min_purchase is not None else None,
            min_quantity=req.min_quantity,
            start_date=req.start_date,
            end_date=req.end_date,
            usage_limit=req.usage_limit,
            times_used=0,
            scope=req.scope,
            product_ids=[PydanticObjectId(pid) for pid in req.product_ids],
            is_active=req.is_active
        )
        await disc.insert()
        return disc

    @staticmethod
    async def update_discount(discount_id: str, req: DiscountUpdate) -> Discount:
        disc = await CatalogService.get_discount(discount_id)
        data = req.model_dump(exclude_unset=True)
        if "value" in data and data["value"] is not None:
            data["value"] = quantize_money(data["value"])
        if "min_purchase" in data and data["min_purchase"] is not None:
            data["min_purchase"] = quantize_money(data["min_purchase"])
        if "product_ids" in data and data["product_ids"] is not None:
            data["product_ids"] = [PydanticObjectId(pid) for pid in data["product_ids"]]
        
        for k, v in data.items():
            setattr(disc, k, v)
        disc.updated_at = datetime.now(timezone.utc)
        await disc.save()
        return disc

    @staticmethod
    async def delete_discount(discount_id: str) -> None:
        disc = await CatalogService.get_discount(discount_id)
        await disc.delete()

    # ----------------- QUOTATION TEMPLATES -----------------
    @staticmethod
    async def list_templates() -> List[QuotationTemplate]:
        return await QuotationTemplate.find_all().sort("+name").to_list()

    @staticmethod
    async def get_template(template_id: str) -> QuotationTemplate:
        tpl = await QuotationTemplate.get(PydanticObjectId(template_id))
        if not tpl:
            raise EntityNotFound(f"Quotation template with id '{template_id}' not found.")
        return tpl

    @staticmethod
    async def create_template(req: QuotationTemplateCreate) -> QuotationTemplate:
        # Verify plan exists
        await CatalogService.get_plan(req.plan_id)
        lines = [
            QuotationTemplateLine(
                product_id=PydanticObjectId(l.product_id),
                variant_id=l.variant_id,
                quantity=l.quantity
            ) for l in req.lines
        ]
        tpl = QuotationTemplate(
            name=req.name.strip(),
            validity_days=req.validity_days,
            plan_id=PydanticObjectId(req.plan_id),
            lines=lines
        )
        await tpl.insert()
        return tpl

    @staticmethod
    async def update_template(template_id: str, req: QuotationTemplateUpdate) -> QuotationTemplate:
        tpl = await CatalogService.get_template(template_id)
        if req.name is not None:
            tpl.name = req.name.strip()
        if req.validity_days is not None:
            tpl.validity_days = req.validity_days
        if req.plan_id is not None:
            await CatalogService.get_plan(req.plan_id)
            tpl.plan_id = PydanticObjectId(req.plan_id)
        if req.lines is not None:
            tpl.lines = [
                QuotationTemplateLine(
                    product_id=PydanticObjectId(l.product_id),
                    variant_id=l.variant_id,
                    quantity=l.quantity
                ) for l in req.lines
            ]
        tpl.updated_at = datetime.now(timezone.utc)
        await tpl.save()
        return tpl

    @staticmethod
    async def delete_template(template_id: str) -> None:
        tpl = await CatalogService.get_template(template_id)
        await tpl.delete()

    # ----------------- CUSTOMERS -----------------
    @staticmethod
    async def list_customers(page: int = 1, page_size: int = 20, q: Optional[str] = None) -> Tuple[List[Customer], int]:
        query = {}
        if q:
            query["name"] = {"$regex": q, "$options": "i"}
        total = await Customer.find(query).count()
        skip = (page - 1) * page_size
        customers = await Customer.find(query).sort("+name").skip(skip).limit(page_size).to_list()
        return customers, total

    @staticmethod
    async def get_customer(customer_id: str) -> Customer:
        cust = await Customer.get(PydanticObjectId(customer_id))
        if not cust:
            raise EntityNotFound(f"Customer with id '{customer_id}' not found.")
        return cust

    @staticmethod
    async def create_customer(req: CustomerCreate) -> Customer:
        cust = Customer(
            user_id=PydanticObjectId(), # Staff/admin manual customer creation can generate new ID
            name=req.name.strip(),
            company=req.company.strip() if req.company else None,
            phone=req.phone.strip() if req.phone else None,
            billing_address=req.billing_address,
            tax_id=req.tax_id.strip() if req.tax_id else None
        )
        await cust.insert()
        return cust

    @staticmethod
    async def update_customer(customer_id: str, req: CustomerUpdate) -> Customer:
        cust = await CatalogService.get_customer(customer_id)
        if req.name is not None:
            cust.name = req.name.strip()
        if req.company is not None:
            cust.company = req.company.strip() if req.company else None
        if req.phone is not None:
            cust.phone = req.phone.strip() if req.phone else None
        if req.billing_address is not None:
            cust.billing_address = req.billing_address
        if req.tax_id is not None:
            cust.tax_id = req.tax_id.strip() if req.tax_id else None
        cust.updated_at = datetime.now(timezone.utc)
        await cust.save()
        return cust

    @staticmethod
    async def delete_customer(customer_id: str) -> None:
        cust = await CatalogService.get_customer(customer_id)
        await cust.delete()
