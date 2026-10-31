from pymongo import ReturnDocument
from app.core.db import get_client
from app.core.config import settings

async def get_next_sequence(name: str) -> int:
    client = get_client()
    db = client[settings.DATABASE_NAME]
    res = await db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return res["seq"]

async def get_next_subscription_number() -> str:
    seq = await get_next_sequence("subscription")
    return f"SUB-{seq:06d}"

async def get_next_invoice_number() -> str:
    seq = await get_next_sequence("invoice")
    return f"INV-{seq:06d}"
