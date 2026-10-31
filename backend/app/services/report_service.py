from datetime import datetime, date, timezone
from decimal import Decimal
from typing import List, Tuple, Dict, Any

from app.core.db import get_client
from app.core.config import settings
from app.core.money import to_decimal, quantize_money, ZERO
from app.models.invoices import Invoice
from app.schemas.reports import (
    ReportSummaryResponse, RevenueReportResponse, MonthlyRevenuePoint
)
from app.services.invoice_service import InvoiceService

class ReportService:
    @staticmethod
    async def get_summary() -> ReportSummaryResponse:
        client = get_client()
        db = client[settings.DATABASE_NAME]

        today = date.today()
        today_dt = datetime.combine(today, datetime.min.time())
        mtd_date = date(today.year, today.month, 1)
        mtd_dt = datetime.combine(mtd_date, datetime.min.time())

        # 1. Active subscriptions count (indexed)
        active_subs = await db.subscriptions.count_documents({"status": "active"})

        # 2. Total revenue collected from payments
        pipe_total_rev = [
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        res_total_rev = await db.payments.aggregate(pipe_total_rev).to_list(length=1)
        rev_total = to_decimal(res_total_rev[0]["total"]) if res_total_rev else ZERO

        # 3. Revenue MTD
        pipe_mtd_rev = [
            {
                "$match": {
                    "$or": [
                        {"paid_on": {"$gte": mtd_dt}},
                        {"paid_on": {"$gte": str(mtd_date)}}
                    ]
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        res_mtd_rev = await db.payments.aggregate(pipe_mtd_rev).to_list(length=1)
        rev_mtd = to_decimal(res_mtd_rev[0]["total"]) if res_mtd_rev else ZERO

        # 4. Outstanding amount across confirmed invoices
        pipe_outstanding = [
            {"$match": {"status": "confirmed"}},
            {"$group": {"_id": None, "total": {"$sum": {"$subtract": ["$total", "$amount_paid"]}}}}
        ]
        res_outstanding = await db.invoices.aggregate(pipe_outstanding).to_list(length=1)
        outstanding = to_decimal(res_outstanding[0]["total"]) if res_outstanding else ZERO

        # 5. Overdue count and overdue amount (indexed match + derived balance)
        pipe_overdue = [
            {
                "$match": {
                    "status": "confirmed",
                    "$or": [
                        {"due_date": {"$lt": today_dt}},
                        {"due_date": {"$lt": str(today)}}
                    ],
                    "$expr": {"$lt": ["$amount_paid", "$total"]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "amount": {"$sum": {"$subtract": ["$total", "$amount_paid"]}}
                }
            }
        ]
        res_overdue = await db.invoices.aggregate(pipe_overdue).to_list(length=1)
        overdue_count = res_overdue[0]["count"] if res_overdue else 0
        overdue_amount = to_decimal(res_overdue[0]["amount"]) if res_overdue else ZERO

        return ReportSummaryResponse(
            active_subscriptions=active_subs,
            revenue_mtd=quantize_money(rev_mtd),
            revenue_total=quantize_money(rev_total),
            outstanding_amount=quantize_money(outstanding),
            overdue_count=overdue_count,
            overdue_amount=quantize_money(overdue_amount)
        )

    @staticmethod
    async def get_revenue_by_month() -> RevenueReportResponse:
        client = get_client()
        db = client[settings.DATABASE_NAME]

        # Aggregate payments grouped by Year-Month string
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "$substr": [
                            {"$dateToString": {"format": "%Y-%m", "date": "$paid_on"}},
                            0,
                            7
                        ]
                    },
                    "revenue": {"$sum": "$amount"}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        results = await db.payments.aggregate(pipeline).to_list(length=36)
        points = []
        for r in results:
            m = r.get("_id")
            if m:
                points.append(MonthlyRevenuePoint(
                    month=str(m),
                    revenue=quantize_money(to_decimal(r.get("revenue", ZERO)))
                ))

        return RevenueReportResponse(points=points)
