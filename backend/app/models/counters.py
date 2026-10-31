from beanie import Document
from pydantic import Field

class Counter(Document):
    id: str = Field(..., alias="_id")
    seq: int = Field(default=0)

    class Settings:
        name = "counters"
