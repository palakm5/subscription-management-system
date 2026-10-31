import pytest
import time
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.db import init_db, close_db

@pytest.mark.asyncio
async def test_kpi_summary_and_lists_performance_under_two_seconds():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Admin login
        res_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@brightloop.com",
            "password": "AdminSecure1!"
        })
        assert res_login.status_code == 200
        token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Assert GET /reports/summary responds in < 2.0s
        t0 = time.perf_counter()
        res_sum = await ac.get("/api/v1/reports/summary", headers=headers)
        duration_sum = time.perf_counter() - t0
        assert res_sum.status_code == 200
        summary_data = res_sum.json()
        assert summary_data["active_subscriptions"] > 0
        print(f"\n[PERF] GET /reports/summary responded in {duration_sum:.4f}s with 10,000+ seeded records.")
        assert duration_sum < 2.0, f"Summary endpoint took {duration_sum:.2f}s (target < 2.0s)"

        # 2. Assert GET /subscriptions responds in < 2.0s
        t0 = time.perf_counter()
        res_subs = await ac.get("/api/v1/subscriptions?page=1&page_size=20", headers=headers)
        duration_subs = time.perf_counter() - t0
        assert res_subs.status_code == 200
        assert res_subs.json()["total"] >= 10000
        print(f"[PERF] GET /subscriptions responded in {duration_subs:.4f}s.")
        assert duration_subs < 2.0

        # 3. Assert GET /invoices responds in < 2.0s
        t0 = time.perf_counter()
        res_invs = await ac.get("/api/v1/invoices?page=1&page_size=20", headers=headers)
        duration_invs = time.perf_counter() - t0
        assert res_invs.status_code == 200
        assert res_invs.json()["total"] >= 20000
        print(f"[PERF] GET /invoices responded in {duration_invs:.4f}s.")
        assert duration_invs < 2.0

        # 4. Assert GET /reports/revenue responds in < 2.0s
        t0 = time.perf_counter()
        res_rev = await ac.get("/api/v1/reports/revenue?group_by=month", headers=headers)
        duration_rev = time.perf_counter() - t0
        assert res_rev.status_code == 200
        print(f"[PERF] GET /reports/revenue responded in {duration_rev:.4f}s.")
        assert duration_rev < 2.0
    await close_db()
