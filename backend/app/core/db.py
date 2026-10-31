import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings

# Import all models
from app.models.users import User
from app.models.customers import Customer
from app.models.products import Product
from app.models.plans import Plan
from app.models.taxes import Tax
from app.models.discounts import Discount
from app.models.quotation_templates import QuotationTemplate
from app.models.counters import Counter
from app.models.subscriptions import Subscription
from app.models.invoices import Invoice
from app.models.payments import Payment
from app.models.audit_log import AuditLog

logger = logging.getLogger("brightloop.db")

client: AsyncIOMotorClient = None

ALL_MODELS = [
    User,
    Customer,
    Product,
    Plan,
    Tax,
    Discount,
    QuotationTemplate,
    Counter,
    Subscription,
    Invoice,
    Payment,
    AuditLog
]

async def init_db():
    global client
    logger.info("Connecting to MongoDB at: %s", settings.MONGODB_URL)
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]
    await init_beanie(database=database, document_models=ALL_MODELS)
    logger.info("Beanie ODM successfully initialized with all document models.")

async def close_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

def get_client() -> AsyncIOMotorClient:
    return client
