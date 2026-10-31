import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.db import init_db, close_db
from app.core.errors import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    duplicate_key_exception_handler,
    generic_exception_handler
)
from app.routers import (
    auth, admin, products, plans, taxes, discounts, quotation_templates,
    customers, subscriptions, billing, invoices, payments, portal, reports
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("brightloop.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Brightloop API...")
    await init_db()
    try:
        from app.services.auth_service import AuthService
        await AuthService.ensure_demo_accounts()
        logger.info("Demo accounts verified and ensured.")
    except Exception as e:
        logger.warning(f"Could not verify demo accounts on startup: {e}")
    yield
    logger.info("Shutting down Brightloop API...")
    await close_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(DuplicateKeyError, duplicate_key_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(taxes.router, prefix="/api/v1")
app.include_router(discounts.router, prefix="/api/v1")
app.include_router(quotation_templates.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(portal.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
@app.get("/docs", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/api/docs")

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "brightloop-api",
        "version": "1.0.0"
    }
