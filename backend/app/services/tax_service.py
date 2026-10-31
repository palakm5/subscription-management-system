from decimal import Decimal
from typing import List, Tuple
from beanie import PydanticObjectId

from app.core.money import quantize_money, pct_money, add_money, ZERO
from app.models.taxes import Tax, TaxType
from app.models.invoices import TaxBreakdownItem

class TaxService:
    @staticmethod
    async def compute_taxes_for_line(
        tax_ids: List[PydanticObjectId],
        post_discount_amount: Decimal
    ) -> Tuple[Decimal, List[TaxBreakdownItem]]:
        if not tax_ids or post_discount_amount <= ZERO:
            return ZERO, []

        taxes = await Tax.find({"_id": {"$in": tax_ids}, "is_active": True}).to_list()
        breakdown: List[TaxBreakdownItem] = []
        total_tax = ZERO

        for t in taxes:
            if t.type == TaxType.PERCENT:
                tax_amt = pct_money(post_discount_amount, t.rate)
            else: # FIXED
                tax_amt = quantize_money(t.rate)
            
            total_tax = add_money(total_tax, tax_amt)
            breakdown.append(TaxBreakdownItem(
                tax_id=t.id,
                name=t.name,
                rate=t.rate,
                amount=tax_amt
            ))

        return total_tax, breakdown
