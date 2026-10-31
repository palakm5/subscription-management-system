import pytest
import pytest_asyncio
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.db import init_db, close_db
from app.models.users import User, UserRole
from app.models.products import Product, Variant
from app.models.plans import Plan, BillingPeriod
from app.models.taxes import Tax, TaxType
from app.models.discounts import Discount, DiscountType, DiscountScope
from app.models.customers import Customer
from app.models.subscriptions import Subscription
from app.models.invoices import Invoice
from app.models.counters import Counter
from app.services.billing_service import BillingService
from app.core.security import hash_password

@pytest_asyncio.fixture(autouse=True)
async def setup_billing_db():
    await init_db()
    await User.find_all().delete()
    await Product.find_all().delete()
    await Plan.find_all().delete()
    await Tax.find_all().delete()
    await Discount.find_all().delete()
    await Customer.find_all().delete()
    await Subscription.find_all().delete()
    await Invoice.find_all().delete()
    await Counter.find_all().delete()
    yield
    await User.find_all().delete()
    await Product.find_all().delete()
    await Plan.find_all().delete()
    await Tax.find_all().delete()
    await Discount.find_all().delete()
    await Customer.find_all().delete()
    await Subscription.find_all().delete()
    await Invoice.find_all().delete()
    await Counter.find_all().delete()
    await close_db()

@pytest.mark.asyncio
async def test_billing_run_and_idempotency():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        admin = User(
            email="admin@brightloop.com",
            password_hash=hash_password("AdminSecure1!"),
            role=UserRole.ADMIN,
            is_active=True
        )
        await admin.insert()

        res_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@brightloop.com",
            "password": "AdminSecure1!"
        })
        token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Setup Tax: 10% VAT
        res_tax = await ac.post("/api/v1/taxes", json={
            "name": "VAT 10%",
            "type": "percent",
            "rate": "10.00"
        }, headers=headers)
        tax_id = res_tax.json()["id"]

        # 2. Setup Product: Base 100.00 with variant +50.00
        res_prod = await ac.post("/api/v1/products", json={
            "name": "Cloud Storage",
            "sales_price": "100.00",
            "tax_ids": [tax_id],
            "variants": [{"attribute": "size", "value": "1TB", "extra_price": "50.00"}]
        }, headers=headers)
        prod_data = res_prod.json()
        prod_id = prod_data["id"]
        var_id = prod_data["variants"][0]["id"]

        # 3. Setup Discount: 10% discount on subscription
        res_disc = await ac.post("/api/v1/discounts", json={
            "name": "SubPromo 10%",
            "type": "percent",
            "value": "10.00",
            "scope": "subscription"
        }, headers=headers)
        disc_id = res_disc.json()["id"]

        # 4. Setup Plan: Monthly
        res_plan = await ac.post("/api/v1/plans", json={
            "name": "Monthly Cloud",
            "price": "10.00",
            "billing_period": "monthly",
            "min_quantity": 1
        }, headers=headers)
        plan_id = res_plan.json()["id"]

        # 5. Setup Customer
        res_cust = await ac.post("/api/v1/customers", json={"name": "Alpha Corp"}, headers=headers)
        cust_id = res_cust.json()["id"]

        # 6. Create Subscription and activate it through state machine
        today = date.today()
        res_sub = await ac.post("/api/v1/subscriptions", json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "start_date": str(today),
            "lines": [{"product_id": prod_id, "variant_id": var_id, "quantity": 1}],
            "discount_ids": [disc_id]
        }, headers=headers)
        sub_id = res_sub.json()["id"]

        # Proper transition sequence: draft -> quotation -> confirmed -> active
        res_t1 = await ac.post(f"/api/v1/subscriptions/{sub_id}/transition", json={"to": "quotation"}, headers=headers)
        assert res_t1.status_code == 200
        res_t2 = await ac.post(f"/api/v1/subscriptions/{sub_id}/transition", json={"to": "confirmed"}, headers=headers)
        assert res_t2.status_code == 200
        res_t3 = await ac.post(f"/api/v1/subscriptions/{sub_id}/transition", json={"to": "active"}, headers=headers)
        assert res_t3.status_code == 200

        # 7. RUN BILLING NOW (POST /billing/run)
        res_bill1 = await ac.post("/api/v1/billing/run", headers=headers)
        assert res_bill1.status_code == 200
        bill1_data = res_bill1.json()
        assert bill1_data["created"] == 1
        assert bill1_data["skipped_duplicates"] == 0

        # Verify generated invoice math:
        # Unit price = 100 + 50 = 150.00
        # Subtotal = 150.00
        # Discount 10% = 15.00 -> remaining 135.00
        # Tax 10% on post-discount 135.00 = 13.50
        # Total = 135.00 + 13.50 = 148.50
        invoices = await Invoice.find_all().to_list()
        assert len(invoices) == 1
        inv = invoices[0]
        assert inv.subtotal == 150.00
        assert inv.discount_total == 15.00
        assert inv.tax_total == 13.50
        assert inv.total == 148.50

        # 8. IDEMPOTENCY TEST: Run billing again immediately -> 0 created, 0 duplicated
        res_bill2 = await ac.post("/api/v1/billing/run", headers=headers)
        assert res_bill2.status_code == 200
        bill2_data = res_bill2.json()
        assert bill2_data["created"] == 0

        # Invoice count in DB must still be EXACTLY 1
        assert await Invoice.count() == 1

@pytest.mark.asyncio
async def test_catch_up_billing():
    # If subscription is 3 periods behind, billing bills each period sequentially without skipping
    today = date.today()
    start_date = today - relativedelta(months=3)

    cust = Customer(name="Beta Industries")
    await cust.insert()

    plan = Plan(name="Monthly Pro", billing_period=BillingPeriod.MONTHLY, min_quantity=1)
    await plan.insert()

    prod = Product(name="Database Service", sales_price=200.00)
    await prod.insert()

    from app.services.sequence_service import get_next_subscription_number
    sub = Subscription(
        number=await get_next_subscription_number(),
        customer_id=cust.id,
        plan_id=plan.id,
        status="active",
        start_date=start_date,
        expiry_date=today + relativedelta(months=6),
        next_invoice_date=start_date, # 3 periods behind
        lines=[
            {
                "product_id": prod.id,
                "product_name": prod.name,
                "quantity": 1,
                "unit_price": 200.00,
                "amount": 200.00
            }
        ]
    )
    await sub.insert()

    # Run catch-up billing
    res = await BillingService.run_billing_job(as_of_date=today)
    # The subscription was claimed and billed iteratively for each period behind
    assert res.created >= 3
    invoices = await Invoice.find(Invoice.subscription_id == sub.id).sort("+period_start").to_list()
    assert len(invoices) >= 3

    # Ensure no period was skipped and all have distinct period_start dates
    starts = [inv.period_start for inv in invoices]
    assert len(starts) == len(set(starts))
