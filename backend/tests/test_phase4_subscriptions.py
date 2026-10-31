import pytest
import pytest_asyncio
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.db import init_db, close_db
from app.models.users import User, UserRole
from app.models.products import Product, Variant
from app.models.plans import Plan, BillingPeriod
from app.models.customers import Customer
from app.models.quotation_templates import QuotationTemplate, QuotationTemplateLine
from app.models.subscriptions import Subscription
from app.models.counters import Counter
from app.core.security import hash_password

@pytest_asyncio.fixture(autouse=True)
async def setup_subscription_db():
    await init_db()
    await User.find_all().delete()
    await Product.find_all().delete()
    await Plan.find_all().delete()
    await Customer.find_all().delete()
    await QuotationTemplate.find_all().delete()
    await Subscription.find_all().delete()
    await Counter.find_all().delete()
    yield
    await User.find_all().delete()
    await Product.find_all().delete()
    await Plan.find_all().delete()
    await Customer.find_all().delete()
    await QuotationTemplate.find_all().delete()
    await Subscription.find_all().delete()
    await Counter.find_all().delete()
    await close_db()

@pytest.mark.asyncio
async def test_subscription_lifecycle_and_numbering():
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

        # Setup Customer
        cust_res = await ac.post("/api/v1/customers", json={"name": "Tesla Motors"}, headers=headers)
        cust_id = cust_res.json()["id"]

        # Setup Product
        prod_res = await ac.post("/api/v1/products", json={
            "name": "Cloud Autopilot Server",
            "sales_price": "500.00",
            "variants": [{"attribute": "tier", "value": "pro", "extra_price": "150.00"}]
        }, headers=headers)
        prod_data = prod_res.json()
        prod_id = prod_data["id"]
        var_id = prod_data["variants"][0]["id"]

        # Setup Plan (monthly, min_qty = 2)
        plan_res = await ac.post("/api/v1/plans", json={
            "name": "Fleet Monthly Plan",
            "price": "20.00",
            "billing_period": "monthly",
            "min_quantity": 2,
            "pausable": True,
            "closable": True,
            "renewable": True
        }, headers=headers)
        plan_id = plan_res.json()["id"]

        # 1. Check min_quantity violation (qty=1 < min_quantity=2)
        res_min_qty_fail = await ac.post("/api/v1/subscriptions", json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "lines": [{"product_id": prod_id, "variant_id": var_id, "quantity": 1}]
        }, headers=headers)
        assert res_min_qty_fail.status_code == 400

        # 2. Create valid subscription from scratch
        res_sub1 = await ac.post("/api/v1/subscriptions", json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "lines": [{"product_id": prod_id, "variant_id": var_id, "quantity": 2}]
        }, headers=headers)
        assert res_sub1.status_code == 201
        sub1_data = res_sub1.json()
        assert sub1_data["number"] == "SUB-000001"
        assert sub1_data["status"] == "draft"
        # Price check: 500 + 150 = 650.00 per unit, total 1300.00
        assert sub1_data["lines"][0]["unit_price"] == "650.00"
        assert sub1_data["lines"][0]["amount"] == "1300.00"
        sub1_id = sub1_data["id"]

        # 3. Create Quotation Template & create Subscription from Template
        tpl_res = await ac.post("/api/v1/quotation-templates", json={
            "name": "Fleet Starter Template",
            "validity_days": 14,
            "plan_id": plan_id,
            "lines": [{"product_id": prod_id, "variant_id": var_id, "quantity": 3}]
        }, headers=headers)
        tpl_id = tpl_res.json()["id"]

        res_sub2 = await ac.post("/api/v1/subscriptions", json={
            "customer_id": cust_id,
            "template_id": tpl_id
        }, headers=headers)
        assert res_sub2.status_code == 201
        sub2_data = res_sub2.json()
        assert sub2_data["number"] == "SUB-000002"
        assert sub2_data["status"] == "quotation"
        assert sub2_data["quotation_valid_until"] is not None
        assert sub2_data["lines"][0]["quantity"] == 3

        # 4. State Transitions on SUB-000001: draft -> quotation -> confirmed -> active
        res_t1 = await ac.post(f"/api/v1/subscriptions/{sub1_id}/transition", json={"to": "quotation"}, headers=headers)
        assert res_t1.status_code == 200
        assert res_t1.json()["status"] == "quotation"

        res_t2 = await ac.post(f"/api/v1/subscriptions/{sub1_id}/transition", json={"to": "confirmed"}, headers=headers)
        assert res_t2.status_code == 200
        assert res_t2.json()["status"] == "confirmed"

        # On confirmed -> active: next_invoice_date = start_date
        res_t3 = await ac.post(f"/api/v1/subscriptions/{sub1_id}/transition", json={"to": "active"}, headers=headers)
        assert res_t3.status_code == 200
        sub_active = res_t3.json()
        assert sub_active["status"] == "active"
        assert sub_active["next_invoice_date"] == sub_active["start_date"]

        # Cannot edit subscription while active (only draft or quotation)
        res_put_forbidden = await ac.put(f"/api/v1/subscriptions/{sub1_id}", json={"payment_terms": 30}, headers=headers)
        assert res_put_forbidden.status_code == 400

        # Pause and resume
        res_pause = await ac.post(f"/api/v1/subscriptions/{sub1_id}/transition", json={"to": "paused"}, headers=headers)
        assert res_pause.status_code == 200
        assert res_pause.json()["status"] == "paused"

        res_resume = await ac.post(f"/api/v1/subscriptions/{sub1_id}/transition", json={"to": "active"}, headers=headers)
        assert res_resume.status_code == 200
        assert res_resume.json()["status"] == "active"

        # Close
        res_close = await ac.post(f"/api/v1/subscriptions/{sub1_id}/transition", json={"to": "closed"}, headers=headers)
        assert res_close.status_code == 200
        assert res_close.json()["status"] == "closed"

        # Renew closed subscription -> creates NEW subscription with sequential number
        res_renew = await ac.post(f"/api/v1/subscriptions/{sub1_id}/renew", headers=headers)
        assert res_renew.status_code == 201
        new_sub = res_renew.json()
        assert new_sub["number"] == "SUB-000003"
        assert new_sub["status"] == "draft"
