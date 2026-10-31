import logging
from app.services.billing_service import BillingService

logger = logging.getLogger("brightloop.worker")

async def scheduled_billing_job():
    logger.info("Executing scheduled recurring billing run...")
    res = await BillingService.run_billing_job()
    logger.info("Billing run finished: %s", res.to_dict())

async def scheduled_auto_close_job():
    logger.info("Executing scheduled auto-close job...")
    closed_count = await BillingService.run_auto_close_job()
    logger.info("Auto-close job finished: %d subscriptions closed.", closed_count)

async def scheduled_quote_expiry_job():
    logger.info("Executing scheduled quotation expiry job...")
    expired_count = await BillingService.run_quote_expiry_job()
    logger.info("Quotation expiry job finished: %d quotations closed.", expired_count)
