import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.db import init_db, close_db
from app.models.users import User, UserRole
from app.models.products import Product
from app.models.plans import Plan
from app.models.taxes import Tax
from app.models.discounts import Discount
from app.models.quotation_templates import QuotationTemplate
from app.models.customers import Customer
from app.core.security import hash_password

@pytest_asyncio.fixture(autouse=True)
async def setup_catalog_db():
    await init_db()
    await User.find_all().delete()
    await Product.find_all().delete()
    await Plan.find_all().delete()
    await Tax.find_all().delete()
    await Discount.find_all().delete()
    await QuotationTemplate.find_all().delete()
    await Customer.find_all().delete()
    yield
    await User.find_all().delete()
    await Product.find_all().delete()
    await Plan.find_all().delete()
    await Tax.find_all().delete()
    await Discount.find_all().delete()
    await QuotationTemplate.find_all().delete()
    await Customer.find_all().delete()
    await close_db()

@pytest.mark.asyncio
async def test_catalog_crud():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create admin user
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
        admin_token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. Create Product with Odoo-brand variant (+560)
        res_prod = await ac.post("/api/v1/products", json={
            "name": "ERP Cloud Suite",
            "type": "service",
            "sales_price": "1000.00",
            "cost_price": "400.00",
            "notes": "Enterprise Cloud Hosting",
            "variants": [
                {
                    "attribute": "brand",
                    "value": "Odoo",
                    "extra_price": "560.00"
                }
            ]
        }, headers=headers)
        assert res_prod.status_code == 201
        prod_data = res_prod.json()
        assert prod_data["name"] == "ERP Cloud Suite"
        assert len(prod_data["variants"]) == 1
        assert prod_data["variants"][0]["attribute"] == "brand"
        assert prod_data["variants"][0]["value"] == "Odoo"
        assert prod_data["variants"][0]["extra_price"] == "560.00"
        product_id = prod_data["id"]

        # 2. Create Plan (monthly, min_qty=1, pausable=True, renewable=True, auto_close=False)
        res_plan = await ac.post("/api/v1/plans", json={
            "name": "Standard Monthly",
            "price": "50.00",
            "billing_period": "monthly",
            "min_quantity": 1,
            "pausable": True,
            "closable": True,
            "renewable": True,
            "auto_close": False
        }, headers=headers)
        assert res_plan.status_code == 201
        plan_data = res_plan.json()
        assert plan_data["billing_period"] == "monthly"
        plan_id = plan_data["id"]

        # 3. Create Tax (percent, 18.00% VAT/GST)
        res_tax = await ac.post("/api/v1/taxes", json={
            "name": "Standard VAT",
            "type": "percent",
            "rate": "18.00"
        }, headers=headers)
        assert res_tax.status_code == 201
        tax_id = res_tax.json()["id"]

        # 4. Create Discount (10% percent discount)
        res_disc = await ac.post("/api/v1/discounts", json={
            "name": "Welcome 10%",
            "type": "percent",
            "value": "10.00",
            "scope": "subscription"
        }, headers=headers)
        assert res_disc.status_code == 201
        disc_id = res_disc.json()["id"]

        # 5. Create Quotation Template
        res_tpl = await ac.post("/api/v1/quotation-templates", json={
            "name": "Standard Enterprise Setup",
            "validity_days": 15,
            "plan_id": plan_id,
            "lines": [
                {
                    "product_id": product_id,
                    "variant_id": prod_data["variants"][0]["id"],
                    "quantity": 2
                }
            ]
        }, headers=headers)
        assert res_tpl.status_code == 201
        tpl_data = res_tpl.json()
        assert tpl_data["validity_days"] == 15
        assert len(tpl_data["lines"]) == 1

        # 6. Create Customer & list with pagination
        res_cust = await ac.post("/api/v1/customers", json={
            "name": "Global Corp Ltd",
            "company": "Global Corp",
            "billing_address": {
                "line1": "100 Market St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105",
                "country": "USA"
            }
        }, headers=headers)
        assert res_cust.status_code == 201
        cust_id = res_cust.json()["id"]

        res_cust_list = await ac.get("/api/v1/customers?page=1&page_size=10", headers=headers)
        assert res_cust_list.status_code == 200
        paged = res_cust_list.json()
        assert paged["total"] == 1
        assert paged["items"][0]["name"] == "Global Corp Ltd"
