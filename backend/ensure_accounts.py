import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.core.db import init_db
from app.services.auth_service import AuthService
from app.models.users import User

async def main():
    await init_db()
    await AuthService.ensure_demo_accounts()
    users = await User.find_all().to_list()
    print("All users now in DB:")
    for u in users:
        print(f"  {u.email} -> {u.role.value}")

if __name__ == "__main__":
    asyncio.run(main())

