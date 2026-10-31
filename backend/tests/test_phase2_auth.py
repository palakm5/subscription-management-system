import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.db import init_db, close_db
from app.models.users import User, UserRole
from app.models.customers import Customer

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    # Clean users and customers before tests
    await User.find_all().delete()
    await Customer.find_all().delete()
    yield
    await User.find_all().delete()
    await Customer.find_all().delete()
    await close_db()

@pytest.mark.asyncio
async def test_auth_signup_and_rbac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Sign up valid customer
        signup_payload = {
            "email": "Customer1@Example.COM",
            "password": "SecurePassword1!",
            "name": "Acme Corp Customer",
            "company": "Acme Corp",
            "phone": "+1-555-0199"
        }
        res = await ac.post("/api/v1/auth/signup", json=signup_payload)
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["user"]["role"] == "customer"
        assert data["user"]["email"] == "customer1@example.com" # Stored lowercased
        assert data["customer"]["name"] == "Acme Corp Customer"
        cust_token = data["access_token"]

        # 2. Duplicate email should fail (case-insensitive)
        res_dup = await ac.post("/api/v1/auth/signup", json=signup_payload)
        assert res_dup.status_code == 409

        # 3. Weak password should fail (< 9 chars, no uppercase, no lowercase, or no special)
        weak_payload = {
            "email": "another@example.com",
            "password": "weak",
            "name": "Weak Pass User"
        }
        res_weak = await ac.post("/api/v1/auth/signup", json=weak_payload)
        assert res_weak.status_code == 400

        # 4. Login with valid credentials
        res_login = await ac.post("/api/v1/auth/login", json={
            "email": "customer1@example.com",
            "password": "SecurePassword1!"
        })
        assert res_login.status_code == 200
        assert res_login.json()["user"]["email"] == "customer1@example.com"

        # 5. Customer cannot create staff (RBAC protection)
        res_staff_forbidden = await ac.post(
            "/api/v1/admin/staff",
            json={"email": "staff1@brightloop.com", "password": "StaffPassword1!", "name": "Staff One"},
            headers={"Authorization": f"Bearer {cust_token}"}
        )
        assert res_staff_forbidden.status_code == 403

        # 6. Create admin directly in DB to test admin-only staff creation
        from app.core.security import hash_password
        admin_user = User(
            email="admin@brightloop.com",
            password_hash=hash_password("AdminSecure1!"),
            role=UserRole.ADMIN,
            is_active=True
        )
        await admin_user.insert()

        res_admin_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@brightloop.com",
            "password": "AdminSecure1!"
        })
        assert res_admin_login.status_code == 200
        admin_token = res_admin_login.json()["access_token"]

        # 7. Admin creates staff
        res_create_staff = await ac.post(
            "/api/v1/admin/staff",
            json={"email": "staff1@brightloop.com", "password": "StaffPassword1!", "name": "Staff One"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res_create_staff.status_code == 201
        staff_data = res_create_staff.json()
        assert staff_data["role"] == "staff"

        # 8. Admin lists staff
        res_list_staff = await ac.get("/api/v1/admin/staff", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_list_staff.status_code == 200
        assert len(res_list_staff.json()) == 1

@pytest.mark.asyncio
async def test_forgot_and_reset_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create user
        signup_payload = {
            "email": "resetme@example.com",
            "password": "InitialPassword1!",
            "name": "Reset Test"
        }
        res = await ac.post("/api/v1/auth/signup", json=signup_payload)
        assert res.status_code == 201

        # Request forgot password
        res_forgot = await ac.post("/api/v1/auth/forgot", json={"email": "resetme@example.com"})
        assert res_forgot.status_code == 200

        # Retrieve user from DB to verify token is hashed
        user = await User.find_one(User.email == "resetme@example.com")
        assert user.reset_token_hash is not None
        assert user.reset_expires_at is not None

        # Reset using direct service helper simulation
        from app.services.auth_service import AuthService
        from app.core.security import generate_random_token, hash_token
        test_raw_token = generate_random_token()
        user.reset_token_hash = hash_token(test_raw_token)
        await user.save()

        # Reset password with valid token
        res_reset = await ac.post("/api/v1/auth/reset", json={
            "token": test_raw_token,
            "new_password": "NewSecretPassword1!"
        })
        assert res_reset.status_code == 200

        # Verify token is invalidated (single-use)
        user_after = await User.find_one(User.email == "resetme@example.com")
        assert user_after.reset_token_hash is None

        # Old password must now fail
        res_login_old = await ac.post("/api/v1/auth/login", json={
            "email": "resetme@example.com",
            "password": "InitialPassword1!"
        })
        assert res_login_old.status_code == 401

        # New password must succeed
        res_login_new = await ac.post("/api/v1/auth/login", json={
            "email": "resetme@example.com",
            "password": "NewSecretPassword1!"
        })
        assert res_login_new.status_code == 200
