from typing import Optional, List
from fastapi import Depends, Header, Cookie, status
from beanie import PydanticObjectId
import jwt

from app.core.security import decode_token
from app.core.errors import AuthenticationFailed, PermissionDenied
from app.models.users import User, UserRole
from app.models.customers import Customer

class TokenData:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role

class CustomerScope:
    def __init__(self, is_customer: bool, customer_id: Optional[PydanticObjectId] = None):
        self.is_customer = is_customer
        self.customer_id = customer_id

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationFailed("Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthenticationFailed("Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationFailed("Token missing subject")
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Access token has expired")
    except Exception:
        raise AuthenticationFailed("Could not validate credentials")

    user = await User.get(PydanticObjectId(user_id))
    if not user or not user.is_active:
        raise AuthenticationFailed("User not found or inactive")
    return user

def require_role(*allowed_roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            raise PermissionDenied(f"User role '{current_user.role.value}' is not authorized for this operation")
        return current_user
    return role_checker

async def current_customer_scope(current_user: User = Depends(get_current_user)) -> CustomerScope:
    """
    Returns row-level customer scoping.
    If the user is a customer, resolves their linked Customer record.
    If the user is admin or staff, customer_id is None (unscoped).
    """
    if current_user.role == UserRole.CUSTOMER:
        customer = await Customer.find_one(Customer.user_id == current_user.id)
        if not customer:
            raise AuthenticationFailed("Customer profile not found for this user")
        return CustomerScope(is_customer=True, customer_id=customer.id)
    return CustomerScope(is_customer=False, customer_id=None)
