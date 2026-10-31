import asyncio
import logging
import random
import time
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from bson import Decimal128, ObjectId
from pymongo import ReturnDocument

from app.core.db import init_db, close_db, get_client
from app.core.config import settings
from app.core.security import hash_password
from app.models.users import UserRole
from app.models.plans import BillingPeriod
from app.models.taxes import TaxType
from app.models.discounts import DiscountType, DiscountScope

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("brightloop.seed")

async def seed_data(sub_count: int = 10000, inv_target: int = 30000):
    start_time = time.time()
    logger.info("Initializing database for seeding...")
    await init_db()

    client = get_client()
    db = client[settings.DATABASE_NAME]

    logger.info("Dropping existing collections to ensure clean seed state...")
    for col in ["users", "customers", "products", "plans", "taxes", "discounts",
                "quotation_templates", "counters", "subscriptions", "invoices", "payments", "audit_log"]:
        await db[col].drop()

    # Re-init indexes
    await init_db()

    # 1. USERS & ROLES
    logger.info("Creating core users: admin, staff, demo customer...")
    admin_id = ObjectId()
    staff_id = ObjectId()
    customer_user_id = ObjectId()

    users_docs = [
        {
            "_id": admin_id,
            "email": "admin@brightloop.com",
            "password_hash": hash_password("AdminSecure1!"),
            "role": UserRole.ADMIN.value,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": staff_id,
            "email": "staff@brightloop.com",
            "password_hash": hash_password("StaffSecure1!"),
            "role": UserRole.STAFF.value,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": customer_user_id,
            "email": "customer@brightloop.com",
            "password_hash": hash_password("CustomerSecure1!"),
            "role": UserRole.CUSTOMER.value,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    await db.users.insert_many(users_docs)

    # 2. CUSTOMERS
    logger.info("Creating primary demo customer and customer pool...")
    primary_customer_id = ObjectId()
    demo_cust = {
        "_id": primary_customer_id,
        "user_id": customer_user_id,
        "name": "Acme Innovations Ltd",
        "company": "Acme Corp",
        "phone": "+1 (555) 019-2831",
        "billing_address": {
            "line1": "456 Innovation Way",
            "city": "Austin",
            "state": "TX",
            "zip": "78701",
            "country": "USA"
        },
        "tax_id": "US-TX-998811",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    # Generate customer pool
    customer_ids = [primary_customer_id]
    customer_docs = [demo_cust]
    first_names = ["Apex", "Vertex", "Summit", "Nexus", "Starlight", "Beacon", "Crest", "Horizon", "Quantum", "Pulse"]
    industries = ["Technologies", "Solutions", "Logistics", "Ventures", "Health", "Financial", "Energy", "Analytics"]

    for i in range(1, 250):
        cid = ObjectId()
        customer_ids.append(cid)
        cname = f"{random.choice(first_names)} {random.choice(industries)} {i}"
        customer_docs.append({
            "_id": cid,
            "user_id": ObjectId(),
            "name": cname,
            "company": cname,
            "phone": f"+1 (555) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "billing_address": {
                "line1": f"{random.randint(10, 999)} Business Park Blvd",
                "city": random.choice(["San Francisco", "New York", "Chicago", "Seattle", "Boston"]),
                "state": random.choice(["CA", "NY", "IL", "WA", "MA"]),
                "zip": f"{random.randint(10000, 99999)}",
                "country": "USA"
            },
            "tax_id": f"TAX-{random.randint(100000, 999999)}",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
    await db.customers.insert_many(customer_docs)

    # 3. TAXES
    logger.info("Creating tax rules...")
    vat_id = ObjectId()
    service_tax_id = ObjectId()
    tax_docs = [
        {
            "_id": vat_id,
            "name": "Standard VAT (18%)",
            "type": TaxType.PERCENT.value,
            "rate": Decimal128("18.00"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": service_tax_id,
            "name": "Tech Service Tax (5%)",
            "type": TaxType.PERCENT.value,
            "rate": Decimal128("5.00"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    await db.taxes.insert_many(tax_docs)

    # 4. DISCOUNTS
    logger.info("Creating promotional discounts...")
    promo10_id = ObjectId()
    disc_docs = [
        {
            "_id": promo10_id,
            "name": "Welcome Discount (10%)",
            "type": DiscountType.PERCENT.value,
            "value": Decimal128("10.00"),
            "min_purchase": Decimal128("100.00"),
            "start_date": None,
            "end_date": None,
            "usage_limit": None,
            "times_used": 0,
            "scope": DiscountScope.SUBSCRIPTION.value,
            "product_ids": [],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    await db.discounts.insert_many(disc_docs)

    # 5. PRODUCTS & VARIANTS
    logger.info("Creating product catalog (including Odoo-brand variant)...")
    erp_id = ObjectId()
    cloud_storage_id = ObjectId()
    api_gateway_id = ObjectId()

    odoo_variant_id = str(ObjectId())

    product_docs = [
        {
            "_id": erp_id,
            "name": "Enterprise ERP Cloud",
            "type": "service",
            "sales_price": Decimal128("1200.00"),
            "cost_price": Decimal128("450.00"),
            "notes": "Full-stack enterprise planning suite with accounting and operations",
            "tax_ids": [vat_id],
            "is_active": True,
            "variants": [
                {
                    "_id": odoo_variant_id,
                    "attribute": "brand",
                    "value": "Odoo",
                    "extra_price": Decimal128("560.00")
                },
                {
                    "_id": str(ObjectId()),
                    "attribute": "deployment",
                    "value": "Dedicated Cluster",
                    "extra_price": Decimal128("350.00")
                }
            ],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": cloud_storage_id,
            "name": "High Availability Object Storage",
            "type": "service",
            "sales_price": Decimal128("150.00"),
            "cost_price": Decimal128("40.00"),
            "notes": "Encrypted S3-compatible cloud bucket with multi-region replication",
            "tax_ids": [vat_id, service_tax_id],
            "is_active": True,
            "variants": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": api_gateway_id,
            "name": "Managed API Gateway Pro",
            "type": "service",
            "sales_price": Decimal128("280.00"),
            "cost_price": Decimal128("75.00"),
            "notes": "Rate-limited SSL reverse proxy with global edge caching",
            "tax_ids": [vat_id],
            "is_active": True,
            "variants": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    await db.products.insert_many(product_docs)

    # 6. PLANS
    logger.info("Creating subscription plans...")
    plan_monthly_id = ObjectId()
    plan_yearly_id = ObjectId()
    plan_docs = [
        {
            "_id": plan_monthly_id,
            "name": "Professional Monthly",
            "price": Decimal128("99.00"),
            "billing_period": BillingPeriod.MONTHLY.value,
            "min_quantity": 1,
            "available_from": None,
            "available_to": None,
            "auto_close": False,
            "closable": True,
            "pausable": True,
            "renewable": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "_id": plan_yearly_id,
            "name": "Enterprise Annual",
            "price": Decimal128("990.00"),
            "billing_period": BillingPeriod.YEARLY.value,
            "min_quantity": 1,
            "available_from": None,
            "available_to": None,
            "auto_close": True,
            "closable": True,
            "pausable": False,
            "renewable": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    await db.plans.insert_many(plan_docs)

    # 7. QUOTATION TEMPLATES
    logger.info("Creating quotation templates...")
    tpl_id = ObjectId()
    tpl_docs = [
        {
            "_id": tpl_id,
            "name": "Standard Enterprise Setup",
            "validity_days": 30,
            "plan_id": plan_monthly_id,
            "lines": [
                {
                    "product_id": erp_id,
                    "variant_id": odoo_variant_id,
                    "quantity": 1
                },
                {
                    "product_id": cloud_storage_id,
                    "variant_id": None,
                    "quantity": 2
                }
            ],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    await db.quotation_templates.insert_many(tpl_docs)

    # 8. BULK SEED SUBSCRIPTIONS (10,000+)
    logger.info("Bulk generating %d subscriptions in high-speed batches...", sub_count)
    today = date.today()
    sub_docs = []
    sub_ids = []
    batch_size = 2500

    # Ensure demo customer has a guaranteed active subscription and confirmed invoice
    demo_sub_id = ObjectId()
    sub_ids.append(demo_sub_id)
    sub_docs.append({
        "_id": demo_sub_id,
        "number": "SUB-000001",
        "customer_id": primary_customer_id,
        "plan_id": plan_monthly_id,
        "template_id": tpl_id,
        "status": "active",
        "start_date": datetime.combine(today - timedelta(days=60), datetime.min.time()),
        "expiry_date": datetime.combine(today + timedelta(days=305), datetime.min.time()),
        "payment_terms": 15,
        "quotation_valid_until": None,
        "next_invoice_date": datetime.combine(today + timedelta(days=30), datetime.min.time()),
        "lock_until": None,
        "locked_by": None,
        "lines": [
            {
                "line_id": str(ObjectId()),
                "product_id": erp_id,
                "product_name": "Enterprise ERP Cloud",
                "variant_id": odoo_variant_id,
                "variant_label": "brand: Odoo",
                "quantity": 1,
                "unit_price": Decimal128("1760.00"),
                "tax_ids": [vat_id],
                "amount": Decimal128("1760.00")
            }
        ],
        "discount_ids": [promo10_id],
        "status_history": [
            {"from": None, "to": "draft", "by": "seed", "at": datetime.now(timezone.utc)},
            {"from": "draft", "to": "quotation", "by": "seed", "at": datetime.now(timezone.utc)},
            {"from": "quotation", "to": "confirmed", "by": "seed", "at": datetime.now(timezone.utc)},
            {"from": "confirmed", "to": "active", "by": "seed", "at": datetime.now(timezone.utc)}
        ],
        "created_at": datetime.now(timezone.utc) - timedelta(days=60),
        "updated_at": datetime.now(timezone.utc)
    })

    # Generate remaining 10,000+ subscriptions
    statuses = ["active", "active", "active", "confirmed", "quotation", "paused", "closed"]
    for i in range(2, sub_count + 1):
        sid = ObjectId()
        sub_ids.append(sid)
        st = random.choice(statuses)
        cid = random.choice(customer_ids)
        start_d = today - timedelta(days=random.randint(15, 360))
        exp_d = start_d + timedelta(days=365)
        nid = start_d + timedelta(days=30)

        sub_docs.append({
            "_id": sid,
            "number": f"SUB-{i:06d}",
            "customer_id": cid,
            "plan_id": plan_monthly_id if i % 4 != 0 else plan_yearly_id,
            "template_id": None,
            "status": st,
            "start_date": datetime.combine(start_d, datetime.min.time()),
            "expiry_date": datetime.combine(exp_d, datetime.min.time()),
            "payment_terms": 15,
            "quotation_valid_until": datetime.combine(start_d + timedelta(days=15), datetime.min.time()) if st == "quotation" else None,
            "next_invoice_date": datetime.combine(nid, datetime.min.time()) if st == "active" else None,
            "lock_until": None,
            "locked_by": None,
            "lines": [
                {
                    "line_id": str(ObjectId()),
                    "product_id": erp_id if i % 2 == 0 else cloud_storage_id,
                    "product_name": "Enterprise ERP Cloud" if i % 2 == 0 else "High Availability Object Storage",
                    "variant_id": odoo_variant_id if i % 2 == 0 else None,
                    "variant_label": "brand: Odoo" if i % 2 == 0 else None,
                    "quantity": random.randint(1, 3),
                    "unit_price": Decimal128("1760.00") if i % 2 == 0 else Decimal128("150.00"),
                    "tax_ids": [vat_id],
                    "amount": Decimal128("1760.00") if i % 2 == 0 else Decimal128("150.00")
                }
            ],
            "discount_ids": [promo10_id] if i % 3 == 0 else [],
            "status_history": [
                {"from": None, "to": st, "by": "seed", "at": datetime.now(timezone.utc)}
            ],
            "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(30, 400)),
            "updated_at": datetime.now(timezone.utc)
        })

        if len(sub_docs) >= batch_size:
            await db.subscriptions.insert_many(sub_docs)
            logger.info("Inserted %d subscriptions...", i)
            sub_docs = []

    if sub_docs:
        await db.subscriptions.insert_many(sub_docs)

    await db.counters.update_one(
        {"_id": "subscription"},
        {"$set": {"seq": sub_count}},
        upsert=True
    )

    # 9. BULK SEED INVOICES & PAYMENTS (30,000+)
    logger.info("Bulk generating %d+ invoices and payment receipts...", inv_target)
    invoice_docs = []
    payment_docs = []
    inv_num = 1

    # Seed 3 invoices per subscription on average
    for sid in sub_ids:
        c_inv_count = random.choice([2, 3, 4])
        for p_idx in range(c_inv_count):
            if inv_num > inv_target:
                break
            inv_id = ObjectId()
            p_start = today - timedelta(days=(c_inv_count - p_idx) * 30)
            p_end = p_start + timedelta(days=29)
            issue_d = p_start
            due_d = issue_d + timedelta(days=15)

            # Determine invoice status distribution
            # 65% paid, 20% confirmed (some overdue), 10% draft, 5% cancelled
            r = random.random()
            if r < 0.65:
                inv_status = "paid"
            elif r < 0.85:
                inv_status = "confirmed"
            elif r < 0.95:
                inv_status = "draft"
            else:
                inv_status = "cancelled"

            subtotal_val = Decimal(random.choice(["150.00", "280.00", "1200.00", "1760.00"]))
            tax_val = subtotal_val * Decimal("0.18")
            total_val = subtotal_val + tax_val

            if inv_status == "paid":
                paid_val = total_val
            elif inv_status == "confirmed":
                paid_val = Decimal(random.choice(["0.00", "0.00", "50.00", "100.00"]))
            else:
                paid_val = Decimal("0.00")

            invoice_docs.append({
                "_id": inv_id,
                "number": f"INV-{inv_num:06d}",
                "subscription_id": sid,
                "customer_id": random.choice(customer_ids),
                "customer_snapshot": {
                    "name": "Enterprise Client",
                    "billing_address": {"line1": "Suite 100", "city": "Dallas", "state": "TX", "zip": "75001", "country": "USA"},
                    "tax_id": "TAX-12345"
                },
                "period_start": datetime.combine(p_start, datetime.min.time()),
                "period_end": datetime.combine(p_end, datetime.min.time()),
                "issue_date": datetime.combine(issue_d, datetime.min.time()),
                "due_date": datetime.combine(due_d, datetime.min.time()),
                "status": inv_status,
                "lines": [
                    {
                        "product_name": "Cloud Infrastructure Service",
                        "variant_label": None,
                        "quantity": 1,
                        "unit_price": Decimal128(subtotal_val),
                        "discount_amount": Decimal128("0.00"),
                        "tax_breakdown": [{"tax_id": vat_id, "name": "VAT 18%", "rate": Decimal128("18.00"), "amount": Decimal128(tax_val)}],
                        "line_total": Decimal128(total_val)
                    }
                ],
                "subtotal": Decimal128(subtotal_val),
                "discount_total": Decimal128("0.00"),
                "tax_total": Decimal128(tax_val),
                "total": Decimal128(total_val),
                "amount_paid": Decimal128(paid_val),
                "applied_discounts": [],
                "sent_at": datetime.now(timezone.utc) if inv_status != "draft" else None,
                "created_at": datetime.combine(issue_d, datetime.min.time()),
                "updated_at": datetime.now(timezone.utc)
            })

            # Record payments for paid/partially-paid invoices
            if paid_val > Decimal("0.00"):
                payment_docs.append({
                    "_id": ObjectId(),
                    "invoice_id": inv_id,
                    "customer_id": random.choice(customer_ids),
                    "method": random.choice(["card", "bank_transfer", "upi"]),
                    "amount": Decimal128(paid_val),
                    "paid_on": datetime.combine(due_d, datetime.min.time()),
                    "note": "Automated payment receipt",
                    "recorded_by": "billing_system",
                    "created_at": datetime.combine(due_d, datetime.min.time()),
                    "updated_at": datetime.combine(due_d, datetime.min.time())
                })

            inv_num += 1

            if len(invoice_docs) >= batch_size:
                await db.invoices.insert_many(invoice_docs)
                if payment_docs:
                    await db.payments.insert_many(payment_docs)
                logger.info("Inserted %d invoices and %d payments...", inv_num, len(payment_docs))
                invoice_docs = []
                payment_docs = []

    if invoice_docs:
        await db.invoices.insert_many(invoice_docs)
    if payment_docs:
        await db.payments.insert_many(payment_docs)

    await db.counters.update_one(
        {"_id": "invoice"},
        {"$set": {"seq": inv_num}},
        upsert=True
    )

    elapsed = time.time() - start_time
    logger.info(
        "Seeding successfully completed in %.2f seconds! %d subscriptions, %d invoices, %d customers.",
        elapsed, sub_count, inv_num, len(customer_ids)
    )
    await close_db()

if __name__ == "__main__":
    asyncio.run(seed_data(10000, 30000))
