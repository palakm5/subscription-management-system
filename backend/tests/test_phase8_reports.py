import pytest
import pytest_asyncio
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.db import init_db, close_db
from app.models.users import User, UserRole
from app.models.customers import Customer
from app.models.subscriptions import Subscription
from app.models.invoices import Invoice, InvoiceStatus, CustomerSnapshot
from app.models.payments import Payment, PaymentMethod
from app.core.security import hash_password

@pytest_asyncio.fixture(autouse=True)
async def setup_reports_db():
    await init_db()
    await User.find_all().delete()
    await Customer.find_all().delete()
    await Subscription.find_all().delete()
    await Invoice.find_all().delete()
    await Payment.find_all().delete()
    yield
    await User.find_all().delete()
    await Customer.find_all().delete()
    await Subscription.find_all().delete()
    await Invoice.find_all().delete()
    await Payment.find_all().delete()
    await close_db()

@pytest.mark.asyncio
async def test_reports_endpoints():
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

        cust = Customer(name="Oracle Systems")
        await cust.insert()

        today = date.today()

        # 1. Active subscription
        from beanie import PydanticObjectId
        sub1 = Subscription(
            number="SUB-REP-01",
            customer_id=cust.id,
            plan_id=PydanticObjectId(),
            status="active",
            start_date=today,
            expiry_date=today + timedelta(days=365)
        )
        await sub1.insert()

        # 2. Confirmed invoice with partial payment (Outstanding balance)
        inv1 = Invoice(
            number="INV-REP-01",
            subscription_id=sub1.id,
            customer_id=cust.id,
            customer_snapshot=CustomerSnapshot(name="Oracle Systems"),
            period_start=today,
            period_end=today + timedelta(days=30),
            issue_date=today,
            due_date=today + timedelta(days=15),
            status=InvoiceStatus.CONFIRMED,
            total=1000.00,
            amount_paid=400.00
        )
        await inv1.insert()

        # Payment for inv1
        pay1 = Payment(
            invoice_id=inv1.id,
            customer_id=cust.id,
            amount=400.00,
            paid_on=today,
            recorded_by="admin@brightloop.com"
        )
        await pay1.insert()

        # 3. Overdue invoice (due_date in past, confirmed, unpaid)
        past_date = today - timedelta(days=5)
        inv_overdue = Invoice(
            number="INV-REP-OVERDUE",
            subscription_id=sub1.id,
            customer_id=cust.id,
            customer_snapshot=CustomerSnapshot(name="Oracle Systems"),
            period_start=past_date - timedelta(days=30),
            period_end=past_date,
            issue_date=past_date - timedelta(days=15),
            due_date=past_date,
            status=InvoiceStatus.CONFIRMED,
            total=350.00,
            amount_paid=0.00
        )
        await inv_overdue.insert()

        # Test GET /reports/summary
        res_sum = await ac.get("/api/v1/reports/summary", headers=headers)
        assert res_sum.status_code == 200
        summary = res_sum.json()
        assert summary["active_subscriptions"] == 1
        assert summary["revenue_total"] == "400.00"
        assert summary["revenue_mtd"] == "400.00"
        # Outstanding = (1000 - 400) + (350 - 0) = 950.00
        assert summary["outstanding_amount"] == "950.00"
        assert summary["overdue_count"] == 1
        assert summary["overdue_amount"] == "350.00"

        # Test GET /reports/revenue?group_by=month
        res_rev = await ac.get("/api/v1/reports/revenue?group_by=month", headers=headers)
        assert res_rev.status_code == 200
        rev_data = res_rev.json()
        assert len(rev_data["points"]) >= 1

        # Test GET /reports/overdue-invoices
        res_overdue = await ac.get("/api/v1/reports/overdue-invoices", headers=headers)
        assert res_overdue.status_code == 200
        overdue_data = res_overdue.json()
        assert overdue_data["total"] == 1
        assert overdue_data["items"][0]["number"] == "INV-REP-OVERDUE"
