import re
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import bcrypt

from app.core.config import settings
from app.core.errors import BusinessRuleViolation

PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9]).{9,}$')

def validate_password_rules(password: str) -> None:
    """
    Enforces password rule:
    More than 8 characters (min 9), at least one uppercase, one lowercase, one special character.
    """
    if len(password) < 9:
        raise BusinessRuleViolation("Password must be more than 8 characters (minimum 9 characters).")
    if not re.search(r'[a-z]', password):
        raise BusinessRuleViolation("Password must contain at least one lowercase letter.")
    if not re.search(r'[A-Z]', password):
        raise BusinessRuleViolation("Password must contain at least one uppercase letter.")
    if not re.search(r'[^a-zA-Z0-9]', password):
        raise BusinessRuleViolation("Password must contain at least one special character.")

def hash_password(password: str) -> str:
    validate_password_rules(password)
    # Direct native bcrypt hashing
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "role": role,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

def generate_random_token() -> str:
    """Generate a high-entropy hex token for password resets."""
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    """Store only a hash of reset tokens in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
