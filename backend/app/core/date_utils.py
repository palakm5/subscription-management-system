from datetime import date
from dateutil.relativedelta import relativedelta
from app.models.plans import BillingPeriod

def add_billing_period(start: date, period: BillingPeriod, count: int = 1) -> date:
    if period == BillingPeriod.DAILY:
        return start + relativedelta(days=count)
    elif period == BillingPeriod.WEEKLY:
        return start + relativedelta(weeks=count)
    elif period == BillingPeriod.MONTHLY:
        return start + relativedelta(months=count)
    elif period == BillingPeriod.YEARLY:
        return start + relativedelta(years=count)
    return start + relativedelta(months=count)

def compute_period_end(start: date, period: BillingPeriod) -> date:
    """End date of one billing period: period_start + 1 period - 1 day (month-end safe)."""
    return add_billing_period(start, period, 1) - relativedelta(days=1)
