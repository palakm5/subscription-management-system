from typing import Dict, Set
from app.core.errors import InvalidTransition, BusinessRuleViolation

SUBSCRIPTION_TRANSITIONS: Dict[str, Set[str]] = {
    "draft": {"quotation", "closed"},
    "quotation": {"confirmed", "draft", "closed"},
    "confirmed": {"active", "closed"},
    "active": {"paused", "closed"},
    "paused": {"active", "closed"},
    "closed": set(),
}

def validate_subscription_transition(from_state: str, to_state: str, plan: any = None) -> None:
    allowed = SUBSCRIPTION_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise InvalidTransition(
            f"Cannot transition subscription from '{from_state}' to '{to_state}'. Allowed transitions: {sorted(list(allowed))}"
        )
    
    if plan:
        if from_state == "active" and to_state == "paused":
            if not getattr(plan, "pausable", True):
                raise BusinessRuleViolation("Plan does not permit pausing this subscription.")
        if from_state == "active" and to_state == "closed":
            if not getattr(plan, "closable", True):
                raise BusinessRuleViolation("Plan does not permit closing this subscription early.")
