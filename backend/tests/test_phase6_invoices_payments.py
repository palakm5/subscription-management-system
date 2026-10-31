import pytest
import pytest_asyncio
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.db import init_db, close_db
from app.models.users import User, UserRole
from app.models.customers import Customer
from app.models.invoices import Invoice, InvoiceStatus, CustomerSnapshot
from app.models.payments import Payment
from app.core.security import hash_password

@pytest_asyncio.fixture(autouse=True)
async def setup_invoices_payments_db():
    await init_db()
    await User.find_all().delete()
    await Customer.find_all().delete()
    await Invoice.find_all().delete()
    await Payment.find_all().delete()
    yield
    await User.find_all().delete()
    await Customer.find_all().delete()
    await Invoice.find_all().delete()
    await Payment.find_all().delete()
    await close_db()

@pytest.mark.asyncio
async def test_invoices_and_payments():
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

        cust = Customer(name="Stark Industries")
        await cust.insert()

        # Create sample invoice
        today = date.today()
        inv = Invoice(
            number="INV-000100",
            subscription_id=cust.id,
            customer_id=cust.id,
            customer_snapshot=CustomerSnapshot(name="Stark Industries"),
            period_start=today,
            period_end=today + timedelta(days=30),
            issue_date=today,
            due_date=today + timedelta(days=15),
            status=InvoiceStatus.DRAFT,
            subtotal=100.00,
            discount_total=0.00,
            tax_total=0.00,
            total=100.00,
            amount_paid=0.00,
            lines=[
                {
                    "product_name": "Arc Reactor Core",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "line_total": 100.00
                }
            ]
        )
        await inv.insert()

        # 1. Cannot pay draft invoice
        res_pay_draft = await ac.post(f"/api/v1/invoices/{inv.id}/payments", json={
            "amount": "50.00",
            "method": "bank_transfer"
        }, headers=headers)
        assert res_pay_draft.status_code == 400

        # 2. Confirm invoice (draft -> confirmed)
        res_confirm = await ac.post(f"/api/v1/invoices/{inv.id}/confirm", headers=headers)
        assert res_confirm.status_code == 200
        assert res_confirm.json()["status"] == "confirmed"

        # 3. Overpayment test (balance is 100, try to pay 150)
        res_overpay = await ac.post(f"/api/v1/invoices/{inv.id}/payments", json={
            "amount": "150.00",
            "method": "bank_transfer"
        }, headers=headers)
        assert res_overpay.status_code == 400

        # 4. Record partial payment (40.00)
        res_partial = await ac.post(f"/api/v1/invoices/{inv.id}/payments", json={
            "amount": "40.00",
            "method": "bank_transfer"
        }, headers=headers)
        assert res_partial.status_code == 201

        # Check invoice: amount_paid = 40.00, balance_due = 60.00, status = confirmed
        res_get_inv = await ac.get(f"/api/v1/invoices/{inv.id}", headers=headers)
        inv_data = res_get_inv.json()
        assert inv_data["amount_paid"] == "40.00"
        assert inv_data["balance_due"] == "60.00"
        assert inv_data["status"] == "confirmed"

        # 5. Complete payment with remaining 60.00 -> flips status to paid
        res_complete = await ac.post(f"/api/v1/invoices/{inv.id}/payments", json={
            "amount": "60.00",
            "method": "card"
        }, headers=headers)
        assert res_complete.status_code == 201

        res_get_paid = await ac.get(f"/api/v1/invoices/{inv.id}", headers=headers)
        paid_data = res_get_paid.json()
        assert paid_data["amount_paid"] == "100.00"
        assert paid_data["balance_due"] == "0.00"
        assert paid_data["status"] == "paid"

        # 6. Test PDF export endpoint
        res_pdf = await ac.get(f"/api/v1/invoices/{inv.id}/pdf", headers=headers)
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"
        assert res_pdf.content.startswith(b"%PDF")

        # 7. Test derived overdue filter
        # Create an overdue invoice (due_date in past, status confirmed, unpaid)
        past_date = today - timedelta(days=10)
        overdue_inv = Invoice(
            number="INV-OVERDUE-01",
            subscription_id=cust.id,
            customer_id=cust.id,
            customer_snapshot=CustomerSnapshot(name="Stark Industries"),
            period_start=past_date - timedelta(days=30),
            period_end=past_date,
            issue_date=past_date - timedelta(days=15),
            due_date=past_date, # In the past
            status=InvoiceStatus.CONFIRMED,
            subtotal=500.00,
            discount_total=0.00,
            tax_total=0.00,
            total=500.00,
            amount_paid=0.00
        )
        await overdue_inv.insert()

        res_overdue_list = await ac.get("/api/v1/invoices?overdue=true", headers=headers)
        assert res_overdue_list.status_code == 200
        overdue_items = res_overdue_list.json()["items"]
        assert len(overdue_items) == 1
        assert overdue_items[0]["number"] == "INV-OVERDUE-01"
        assert overdue_items[0]["is_overdue"] is True
