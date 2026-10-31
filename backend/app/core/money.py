from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional, Annotated
from bson import Decimal128
from pydantic import BeforeValidator, PlainSerializer

TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0.00")

def to_decimal(val: Union[Decimal, Decimal128, str, int, float, None]) -> Decimal:
    """Safely convert any numeric representation to Decimal."""
    if val is None:
        return ZERO
    if isinstance(val, Decimal):
        return val
    if isinstance(val, Decimal128):
        return val.to_decimal()
    if isinstance(val, (int, str)):
        return Decimal(str(val))
    if isinstance(val, float):
        return Decimal(f"{val:.6f}")
    return Decimal(str(val))

def quantize_money(val: Union[Decimal, Decimal128, str, int, float, None]) -> Decimal:
    """Round to 2 decimal places using standard financial ROUND_HALF_UP."""
    d = to_decimal(val)
    return d.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

def to_decimal128(val: Union[Decimal, Decimal128, str, int, float, None]) -> Decimal128:
    """Format and convert value to BSON Decimal128 for MongoDB storage."""
    d = quantize_money(val)
    return Decimal128(d)

def add_money(*vals: Union[Decimal, Decimal128, str, int, float, None]) -> Decimal:
    """Sum multiple monetary values with 2-decimal precision."""
    total = sum((to_decimal(v) for v in vals), ZERO)
    return quantize_money(total)

def sub_money(a: Union[Decimal, Decimal128, str, int, float, None],
              b: Union[Decimal, Decimal128, str, int, float, None]) -> Decimal:
    """Subtract b from a with 2-decimal precision."""
    return quantize_money(to_decimal(a) - to_decimal(b))

def mul_money(a: Union[Decimal, Decimal128, str, int, float, None],
              qty: Union[Decimal, Decimal128, str, int, float, None]) -> Decimal:
    """Multiply monetary value by quantity/multiplier with 2-decimal precision."""
    return quantize_money(to_decimal(a) * to_decimal(qty))

def div_money(a: Union[Decimal, Decimal128, str, int, float, None],
              b: Union[Decimal, Decimal128, str, int, float, None]) -> Decimal:
    """Divide a by b with 2-decimal precision."""
    denom = to_decimal(b)
    if denom == ZERO:
        raise ZeroDivisionError("Cannot divide money by zero")
    return quantize_money(to_decimal(a) / denom)

def pct_money(base: Union[Decimal, Decimal128, str, int, float, None],
              pct: Union[Decimal, Decimal128, str, int, float, None]) -> Decimal:
    """Calculate percentage of an amount (e.g., base * pct / 100)."""
    return quantize_money((to_decimal(base) * to_decimal(pct)) / Decimal("100"))

def validate_money(v: any) -> Decimal:
    if v is None:
        return ZERO
    return quantize_money(v)

def validate_optional_money(v: any) -> Optional[Decimal]:
    if v is None:
        return None
    return quantize_money(v)

Money = Annotated[
    Decimal,
    BeforeValidator(validate_money),
    PlainSerializer(lambda x: str(quantize_money(x)), return_type=str, when_used="json")
]

OptionalMoney = Annotated[
    Optional[Decimal],
    BeforeValidator(validate_optional_money),
    PlainSerializer(lambda x: str(quantize_money(x)) if x is not None else None, return_type=str, when_used="json")
]
