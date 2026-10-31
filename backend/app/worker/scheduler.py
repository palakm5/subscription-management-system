import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.db import init_db, close_db
from app.worker.jobs import (
    scheduled_billing_job,
    scheduled_auto_close_job,
    scheduled_quote_expiry_job
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("brightloop.scheduler")

async def main():
    logger.info("Initializing worker process and database connection...")
    await init_db()

    scheduler = AsyncIOScheduler()

    # Recurring billing run at 02:00 UTC daily
    scheduler.add_job(
        scheduled_billing_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_billing_run",
        replace_existing=True
    )

    # Auto-close expired subscriptions daily at 01:00 UTC
    scheduler.add_job(
        scheduled_auto_close_job,
        trigger=CronTrigger(hour=1, minute=0),
        id="daily_auto_close",
        replace_existing=True
    )

    # Quotation expiry daily at 00:30 UTC
    scheduler.add_job(
        scheduled_quote_expiry_job,
        trigger=CronTrigger(hour=0, minute=30),
        id="daily_quote_expiry",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Brightloop background worker scheduler started successfully.")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down worker process...")
        scheduler.shutdown()
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
