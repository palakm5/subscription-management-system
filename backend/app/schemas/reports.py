from decimal import Decimal
from typing import List
from pydantic import BaseModel
from app.core.money import ZERO

class ReportSummaryResponse(BaseModel):
    active_subscriptions: int
    revenue_mtd: Decimal
    revenue_total: Decimal
    outstanding_amount: Decimal
    overdue_count: int
    overdue_amount: Decimal

class MonthlyRevenuePoint(BaseModel):
    month: str # "YYYY-MM"
    revenue: Decimal

class RevenueReportResponse(BaseModel):
    points: List[MonthlyRevenuePoint]
