import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.core.db import init_db
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest

async def main():
    await init_db()
    for email, pwd in [
        ("admin@brightloop.com", "AdminSecure1!"),
        ("staff@brightloop.com", "StaffSecure1!"),
        ("customer@brightloop.com", "CustomerSecure1!"),
    ]:
        try:
            token, refresh, user, cust = await AuthService.login(LoginRequest(email=email, password=pwd))
            print(f"SUCCESS: {email} logged in as {user.role.value}")
        except Exception as e:
            print(f"FAILED: {email} -> {e}")

if __name__ == "__main__":
    asyncio.run(main())

