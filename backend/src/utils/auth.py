import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from src.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain text password against a hashed password."""
    return pwd_context.verify(plain, hashed)


def create_access_token(
    user_id: str,
    email: str,
    username: str,
    extra_claims: Optional[dict] = None,
    expire_minutes: Optional[int] = None,
) -> str:
    """
    Create a signed JWT access token.

    extra_claims  — optional extra fields merged into the payload.
                    Used for 2FA: {"2fa_pending": True}
    expire_minutes — override default expiry. Used for temp tokens (5 min).
    """
    expire = timedelta(minutes=expire_minutes if expire_minutes else settings.JWT_EXPIRE_MINUTES)

    payload = {
        "user_id": user_id,        # used by auth_deps.py to fetch user
        "sub": user_id,            # kept for backward compatibility
        "email": email,
        "username": username,
        "exp": datetime.now(timezone.utc) + expire,
    }

    # Merge any extra claims (e.g. 2fa_pending: True for temp tokens)
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    Raises jose.JWTError if the token is invalid or expired.
    Used by /verify-2fa to decode the temp token.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def _hash_token(raw_token: str) -> str:
    """Return the SHA-256 hash of a raw token."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def hash_reset_token(raw_token: str) -> str:
    """Hash a reset token using SHA-256 for safe database lookup."""
    return _hash_token(raw_token)


def hash_refresh_token(raw_token: str) -> str:
    """Hash a refresh token using SHA-256 for safe database lookup."""
    return _hash_token(raw_token)


def generate_reset_token() -> tuple[str, str]:
    """Generate a URL-safe reset token and its SHA-256 hash."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    return raw_token, token_hash


def generate_refresh_token() -> tuple[str, str]:
    """Generate a URL-safe refresh token and its SHA-256 hash."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    return raw_token, token_hash


# Alias — keeps any existing code using decode_token() working
def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate human-friendly backup codes in XXXX-XXXX format."""
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(4).upper()
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def hash_backup_code(code: str) -> str:
    """Normalize and hash a backup code for secure storage."""
    normalized = code.strip().upper()
    return hashlib.sha256(normalized.encode()).hexdigest()


# Alias — keeps any existing code using decode_token() working
decode_token = decode_access_token