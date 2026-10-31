from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from beanie import PydanticObjectId

from app.core.money import quantize_money, pct_money, sub_money, ZERO
from app.models.discounts import Discount, DiscountType, DiscountScope
from app.models.subscriptions import SubscriptionLine

class DiscountService:
    @staticmethod
    def is_eligible(
        discount: Discount,
        as_of_date: date,
        base_amount: Decimal,
        total_quantity: int
    ) -> bool:
        if not discount.is_active:
            return False
        if discount.start_date and as_of_date < discount.start_date:
            return False
        if discount.end_date and as_of_date > discount.end_date:
            return False
        if discount.usage_limit is not None and discount.times_used >= discount.usage_limit:
            return False
        if discount.min_purchase is not None and base_amount < discount.min_purchase:
            return False
        if discount.min_quantity is not None and total_quantity < discount.min_quantity:
            return False
        return True

    @staticmethod
    def calculate_discount_amount(discount: Discount, base_amount: Decimal) -> Decimal:
        if base_amount <= ZERO:
            return ZERO
        
        if discount.type == DiscountType.PERCENT:
            amount = pct_money(base_amount, discount.value)
        else: # FIXED
            amount = quantize_money(discount.value)

        # Discount must never exceed the base amount
        return min(amount, base_amount)
