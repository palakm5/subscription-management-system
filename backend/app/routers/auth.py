from typing import Optional
from fastapi import APIRouter, Response, Request, Cookie, Depends, status

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    AuthResponse,
    UserResponse,
    CustomerResponse,
    MessageResponse
)
from app.services.auth_service import AuthService
from app.core.deps import get_current_user
from app.models.users import User, UserRole
from app.models.customers import Customer
from app.core.errors import AuthenticationFailed

router = APIRouter(prefix="/auth", tags=["auth"])

def set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False, # Set True in HTTPS prod
        max_age=7 * 24 * 3600,
        path="/"
    )

def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
    )

def to_customer_response(customer: Optional[Customer]) -> Optional[CustomerResponse]:
    if not customer:
        return None
    return CustomerResponse(
        id=str(customer.id),
        user_id=str(customer.user_id),
        name=customer.name,
        company=customer.company,
        phone=customer.phone,
        billing_address=customer.billing_address,
        tax_id=customer.tax_id
    )

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest, response: Response):
    access_token, refresh_token, user, customer = await AuthService.signup(req)
    set_refresh_cookie(response, refresh_token)
    return AuthResponse(
        access_token=access_token,
        user=to_user_response(user),
        customer=to_customer_response(customer)
    )

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, response: Response):
    access_token, refresh_token, user, customer = await AuthService.login(req)
    set_refresh_cookie(response, refresh_token)
    return AuthResponse(
        access_token=access_token,
        user=to_user_response(user),
        customer=to_customer_response(customer)
    )

@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    response: Response,
    request: Request,
    refresh_token: Optional[str] = Cookie(None)
):
    # Support cookie or Authorization / body
    token = refresh_token
    if not token:
        # Check header if cookie is blocked
        auth_hdr = request.headers.get("x-refresh-token")
        if auth_hdr:
            token = auth_hdr
    if not token:
        raise AuthenticationFailed("Refresh token missing.")

    new_access, new_refresh, user, customer = await AuthService.refresh_tokens(token)
    set_refresh_cookie(response, new_refresh)
    return AuthResponse(
        access_token=new_access,
        user=to_user_response(user),
        customer=to_customer_response(customer)
    )

@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    response.delete_cookie(key="refresh_token", path="/")
    return MessageResponse(message="Logged out successfully.")

@router.post("/forgot", response_model=MessageResponse)
async def forgot_password(req: ForgotPasswordRequest):
    await AuthService.forgot_password(req.email)
    return MessageResponse(message="If an account matches this email, a reset link has been dispatched.")

@router.post("/reset", response_model=MessageResponse)
async def reset_password(req: ResetPasswordRequest):
    await AuthService.reset_password(req)
    return MessageResponse(message="Password reset successfully. You can now log in.")

@router.get("/me", response_model=AuthResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    customer = None
    if current_user.role == UserRole.CUSTOMER:
        customer = await Customer.find_one(Customer.user_id == current_user.id)
    return AuthResponse(
        access_token="",
        user=to_user_response(current_user),
        customer=to_customer_response(customer)
    )
