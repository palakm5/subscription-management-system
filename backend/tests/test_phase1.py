import pytest
from decimal import Decimal
from app.core.money import quantize_money, add_money, sub_money, mul_money, div_money, pct_money
from app.core.security import validate_password_rules, hash_password, verify_password
from app.core.errors import BusinessRuleViolation, InvalidTransition
from app.state.subscription_fsm import validate_subscription_transition
from app.state.invoice_fsm import validate_invoice_transition

def test_money_calculations():
    # Never use floats for money, 2 dp rounding ROUND_HALF_UP
    assert quantize_money("10.005") == Decimal("10.01")
    assert quantize_money("10.004") == Decimal("10.00")
    assert add_money("10.50", "20.25") == Decimal("30.75")
    assert sub_money("100.00", "25.50") == Decimal("74.50")
    assert mul_money("15.50", 3) == Decimal("46.50")
    assert div_money("100.00", 3) == Decimal("33.33")
    assert pct_money("250.00", "10") == Decimal("25.00")

def test_password_policy():
    # Password: more than 8 characters (min 9), at least one uppercase, one lowercase, one special character
    with pytest.raises(BusinessRuleViolation):
        validate_password_rules("Short1!") # 8 chars - fails
    with pytest.raises(BusinessRuleViolation):
        validate_password_rules("alllowercase1!") # no uppercase - fails
    with pytest.raises(BusinessRuleViolation):
        validate_password_rules("ALLUPPERCASE1!") # no lowercase - fails
    with pytest.raises(BusinessRuleViolation):
        validate_password_rules("NoSpecial123") # no special - fails
    
    # Valid password:
    valid_pass = "ValidP@ss1"
    validate_password_rules(valid_pass)
    hashed = hash_password(valid_pass)
    assert verify_password(valid_pass, hashed)
    assert not verify_password("WrongPassword1!", hashed)

def test_fsm_transitions():
    # Subscriptions
    validate_subscription_transition("draft", "quotation")
    validate_subscription_transition("quotation", "confirmed")
    validate_subscription_transition("confirmed", "active")
    validate_subscription_transition("active", "paused")
    validate_subscription_transition("paused", "active")
    validate_subscription_transition("active", "closed")

    with pytest.raises(InvalidTransition):
        validate_subscription_transition("draft", "active") # Cannot jump directly
    with pytest.raises(InvalidTransition):
        validate_subscription_transition("closed", "active") # Closed cannot transition

    # Invoices
    validate_invoice_transition("draft", "confirmed")
    validate_invoice_transition("confirmed", "paid")
    validate_invoice_transition("confirmed", "cancelled")
    
    with pytest.raises(InvalidTransition):
        validate_invoice_transition("paid", "cancelled") # Paid cannot cancel
