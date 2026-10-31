from decimal import Decimal
from typing import Dict, Any, List
from app.core.money import quantize_money, mul_money

def compute_line_subtotal(quantity: int, unit_price: Decimal) -> Decimal:
    """Calculate subtotal for an invoice line (qty * unit_price)."""
    return mul_money(unit_price, quantity)
