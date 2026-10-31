from typing import Dict, Set
from app.core.errors import InvalidTransition

INVOICE_TRANSITIONS: Dict[str, Set[str]] = {
    "draft": {"confirmed", "cancelled"},
    "confirmed": {"paid", "cancelled"},
    "paid": set(),
    "cancelled": set(),
}

def validate_invoice_transition(from_state: str, to_state: str) -> None:
    allowed = INVOICE_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise InvalidTransition(
            f"Cannot transition invoice from '{from_state}' to '{to_state}'. Allowed transitions: {sorted(list(allowed))}"
        )
