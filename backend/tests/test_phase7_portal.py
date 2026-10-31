import pytest
import pytest_asyncio
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.db import init_db, close_db
from app.models.users import User
from app.models.customers import Customer
from app.models.plans import Plan, BillingPeriod
from app.models.products import Product
from app.models.subscriptions import Subscription
from app.models.invoices import Invoice, InvoiceStatus, CustomerSnapshot

@pytest_asyncio.fixture(autouse=True)
async def setup_portal_db():
    await init_db()
    await User.find_all().delete()
    await Customer.find_all().delete()
    await Plan.find_all().delete()
    await Product.find_all().delete()
    await Subscription.find_all().delete()
    await Invoice.find_all().delete()
    yield
    await User.find_all().delete()
    await Customer.find_all().delete()
    await Plan.find_all().delete()
    await Product.find_all().delete()
    await Subscription.find_all().delete()
    await Invoice.find_all().delete()
    await close_db()

@pytest.mark.asyncio
async def test_portal_isolation_and_row_scope():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Sign up Customer A
        res_a = await ac.post("/api/v1/auth/signup", json={
            "email": "customerA@example.com",
            "password": "PasswordA1!",
            "name": "Customer Alice"
        })
        assert res_a.status_code == 201
        token_a = res_a.json()["access_token"]
        cust_a_id = res_a.json()["customer"]["id"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 2. Sign up Customer B
        res_b = await ac.post("/api/v1/auth/signup", json={
            "email": "customerB@example.com",
            "password": "PasswordB1!",
            "name": "Customer Bob"
        })
        assert res_b.status_code == 201
        token_b = res_b.json()["access_token"]
        cust_b_id = res_b.json()["customer"]["id"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Create Plan & Product
        plan = Plan(name="Cloud Plus", billing_period=BillingPeriod.MONTHLY, pausable=True, closable=True)
        await plan.insert()
        prod = Product(name="Storage Node", sales_price=50.00)
        await prod.insert()

        from app.services.sequence_service import get_next_subscription_number
        from beanie import PydanticObjectId

        # Create Subscription for Customer A
        sub_a = Subscription(
            number=await get_next_subscription_number(),
            customer_id=PydanticObjectId(cust_a_id),
            plan_id=plan.id,
            status="active",
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365)
        )
        await sub_a.insert()

        # Create Subscription for Customer B
        sub_b = Subscription(
            number=await get_next_subscription_number(),
            customer_id=PydanticObjectId(cust_b_id),
            plan_id=plan.id,
            status="active",
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365)
        )
        await sub_b.insert()

        # Create Invoice for Customer B
        inv_b = Invoice(
            number="INV-B-001",
            subscription_id=sub_b.id,
            customer_id=PydanticObjectId(cust_b_id),
            customer_snapshot=CustomerSnapshot(name="Customer Bob"),
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=15),
            status=InvoiceStatus.CONFIRMED,
            total=50.00
        )
        await inv_b.insert()

        # 3. Customer A queries /portal/subscriptions: only sees their own
        res_list_a = await ac.get("/api/v1/portal/subscriptions", headers=headers_a)
        assert res_list_a.status_code == 200
        items_a = res_list_a.json()["items"]
        assert len(items_a) == 1
        assert items_a[0]["id"] == str(sub_a.id)

        # 4. ROW LEVEL SECURITY RULE:
        # When Customer A requests Customer B's subscription, must return 404 (NOT 403)
        res_cross_sub = await ac.get(f"/api/v1/portal/subscriptions/{sub_b.id}", headers=headers_a)
        assert res_cross_sub.status_code == 404

        # When Customer A requests Customer B's invoice, must return 404 (NOT 403)
        res_cross_inv = await ac.get(f"/api/v1/portal/invoices/{inv_b.id}", headers=headers_a)
        assert res_cross_inv.status_code == 404

        # When Customer A requests Customer B's PDF, must return 404
        res_cross_pdf = await ac.get(f"/api/v1/portal/invoices/{inv_b.id}/pdf", headers=headers_a)
        assert res_cross_pdf.status_code == 404

        # 5. Customer A pauses their own subscription
        res_pause_a = await ac.post(
            f"/api/v1/portal/subscriptions/{sub_a.id}/transition",
            json={"to": "paused"},
            headers=headers_a
        )
        assert res_pause_a.status_code == 200
        assert res_pause_a.json()["status"] == "paused"
