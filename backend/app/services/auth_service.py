from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from beanie import PydanticObjectId
import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_random_token,
    hash_token
)
from app.core.config import settings
from app.core.errors import (
    DuplicateEntity,
    AuthenticationFailed,
    BusinessRuleViolation,
    EntityNotFound
)
from app.models.users import User, UserRole
from app.models.customers import Customer, BillingAddress
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    ResetPasswordRequest,
    CreateStaffRequest
)
from app.services.email_service import send_reset_password_email

class AuthService:
    @staticmethod
    async def signup(req: SignupRequest) -> Tuple[str, str, User, Customer]:
        # Email uniqueness check (case-insensitive via lowercased store)
        normalized_email = req.email.lower().strip()
        existing = await User.find_one(User.email == normalized_email)
        if existing:
            raise DuplicateEntity(f"An account with email '{normalized_email}' already exists.")

        # Hash password (enforcing password strength rule)
        pw_hash = hash_password(req.password)

        # Public signup ALWAYS creates role = customer
        user = User(
            email=normalized_email,
            password_hash=pw_hash,
            role=UserRole.CUSTOMER,
            is_active=True
        )
        await user.insert()

        customer = Customer(
            user_id=user.id,
            name=req.name.strip(),
            company=req.company.strip() if req.company else None,
            phone=req.phone.strip() if req.phone else None,
            billing_address=req.billing_address or BillingAddress(),
            tax_id=req.tax_id.strip() if req.tax_id else None
        )
        await customer.insert()

        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id), user.role.value)
        return access_token, refresh_token, user, customer

    @staticmethod
    async def login(req: LoginRequest) -> Tuple[str, str, User, Optional[Customer]]:
        normalized_email = req.email.lower().strip()
        user = await User.find_one(User.email == normalized_email)
        if not user or not user.is_active:
            raise AuthenticationFailed("Invalid email or password.")
        
        if not verify_password(req.password, user.password_hash):
            raise AuthenticationFailed("Invalid email or password.")

        customer = None
        if user.role == UserRole.CUSTOMER:
            customer = await Customer.find_one(Customer.user_id == user.id)

        access_token = create_access_token(str(user.id), user.role.value)
        refresh_token = create_refresh_token(str(user.id), user.role.value)
        return access_token, refresh_token, user, customer

    @staticmethod
    async def refresh_tokens(refresh_token: str) -> Tuple[str, str, User, Optional[Customer]]:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationFailed("Invalid token type for refresh.")
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationFailed("Token missing subject.")
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Refresh token has expired.")
        except Exception:
            raise AuthenticationFailed("Invalid refresh token.")

        user = await User.get(PydanticObjectId(user_id))
        if not user or not user.is_active:
            raise AuthenticationFailed("User account is inactive or not found.")

        customer = None
        if user.role == UserRole.CUSTOMER:
            customer = await Customer.find_one(Customer.user_id == user.id)

        new_access = create_access_token(str(user.id), user.role.value)
        new_refresh = create_refresh_token(str(user.id), user.role.value)
        return new_access, new_refresh, user, customer

    @staticmethod
    async def forgot_password(email: str) -> None:
        normalized_email = email.lower().strip()
        user = await User.find_one(User.email == normalized_email)
        # Always return 200 to prevent email enumeration attacks
        if not user or not user.is_active:
            return

        raw_token = generate_random_token()
        token_hash = hash_token(raw_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

        user.reset_token_hash = token_hash
        user.reset_expires_at = expires_at
        user.updated_at = now
        await user.save()

        await send_reset_password_email(user.email, raw_token)

    @staticmethod
    async def reset_password(req: ResetPasswordRequest) -> None:
        token_hash = hash_token(req.token)
        now = datetime.now(timezone.utc)

        user = await User.find_one(
            User.reset_token_hash == token_hash,
            User.reset_expires_at > now
        )
        if not user:
            raise BusinessRuleViolation("Reset token is invalid or has expired.")

        # Hash new password (rule validation happens inside hash_password)
        new_pw_hash = hash_password(req.new_password)

        # Clear token and expiry on single-use
        user.password_hash = new_pw_hash
        user.reset_token_hash = None
        user.reset_expires_at = None
        user.updated_at = now
        await user.save()

    @staticmethod
    async def create_staff(req: CreateStaffRequest) -> User:
        normalized_email = req.email.lower().strip()
        existing = await User.find_one(User.email == normalized_email)
        if existing:
            raise DuplicateEntity(f"A user with email '{normalized_email}' already exists.")

        pw_hash = hash_password(req.password)
        staff_user = User(
            email=normalized_email,
            password_hash=pw_hash,
            role=UserRole.STAFF,
            is_active=True
        )
        await staff_user.insert()
        return staff_user

    @staticmethod
    async def ensure_demo_accounts():
        """Ensure admin, staff, and customer demo accounts always exist with guaranteed credentials."""
        accounts = [
            ("admin@brightloop.com", "AdminSecure1!", UserRole.ADMIN, "Brightloop Admin", "Brightloop HQ"),
            ("staff@brightloop.com", "StaffSecure1!", UserRole.STAFF, "Brightloop Staff", "Brightloop Operations"),
            ("customer@brightloop.com", "CustomerSecure1!", UserRole.CUSTOMER, "Acme Customer Corp", "Acme Corp"),
        ]
        for email, pwd, role, cust_name, cust_company in accounts:
            normalized = email.lower().strip()
            user = await User.find_one(User.email == normalized)
            pw_hash = hash_password(pwd)
            if not user:
                user = User(
                    email=normalized,
                    password_hash=pw_hash,
                    role=role,
                    is_active=True
                )
                await user.insert()
            else:
                user.password_hash = pw_hash
                user.role = role
                user.is_active = True
                await user.save()

            if role == UserRole.CUSTOMER:
                customer = await Customer.find_one(Customer.user_id == user.id)
                if not customer:
                    customer = Customer(
                        user_id=user.id,
                        name=cust_name,
                        company=cust_company,
                        phone="+1 (555) 019-2831",
                        billing_address=BillingAddress(
                            line1="456 Innovation Way",
                            city="Austin",
                            state="Texas",
                            zip="78701",
                            country="United States"
                        ),
                        tax_id="US-TX-998811"
                    )
                    await customer.insert()

