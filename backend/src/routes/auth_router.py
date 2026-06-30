from uuid import uuid4

import pyotp
import qrcode
import io
import base64

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError

from src.config.database import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    enable_user_2fa,
    disable_user_2fa,
)
from src.config.settings import settings
from src.utils.auth import create_access_token, hash_password, verify_password, decode_access_token
from src.utils.auth_deps import get_current_user
from src.utils.logger import logger

router = APIRouter()
bearer_scheme = HTTPBearer()


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    username: str


class LoginResponse(BaseModel):
    """
    Login now returns either:
      - A full AuthResponse (if 2FA is disabled)
      - A temp_token + requires_2fa flag (if 2FA is enabled)
    We use a flexible dict response for login.
    """
    pass


class Enable2FAResponse(BaseModel):
    qr_code_url: str     # base64 PNG — render in <img> tag
    totp_secret: str     # manual fallback for Google Authenticator


class Verify2FARequest(BaseModel):
    temp_token: str      # short-lived token from /login
    otp_code: str        # 6-digit code from Google Authenticator


# ── TOTP helpers (local to this router) ──────────────────────────────────────

def _generate_totp_secret() -> str:
    return pyotp.random_base32()


def _get_totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.TOTP_ISSUER
    )


def _verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code)


def _generate_qr_base64(uri: str) -> str:
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── 1. REGISTER ───────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register_user(payload: RegisterRequest) -> AuthResponse:
    """Create a new user account and return a JWT access token."""
    if await get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await get_user_by_username(payload.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user_id = str(uuid4())
    await create_user(user_id, payload.email, payload.username, hash_password(payload.password))

    access_token = create_access_token(
        user_id=user_id,
        email=payload.email,
        username=payload.username,
    )
    logger.info(f"New user registered: {payload.email}")

    return AuthResponse(
        access_token=access_token,
        user_id=user_id,
        email=payload.email,
        username=payload.username,
    )


# ── 2. LOGIN ──────────────────────────────────────────────────────────────────

@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user.
    - If 2FA is disabled  → return full access token (same as before)
    - If 2FA is enabled   → return temp_token (valid 5 min), user must verify OTP
    """
    user = None
    if "@" in form_data.username:
        user = await get_user_by_email(form_data.username)
    else:
        user = await get_user_by_username(form_data.username)

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")

    # ── 2FA enabled: issue temp token ─────────────────
    if user.get("is_2fa_enabled"):
        temp_token = create_access_token(
            user_id=user["id"],
            email=user["email"],
            username=user["username"],
            extra_claims={"2fa_pending": True},
            expire_minutes=settings.OTP_EXPIRE_MINUTES,   # 5 min only
        )
        logger.info(f"2FA required for: {user['email']}")
        return {
            "requires_2fa": True,
            "temp_token": temp_token,
            "message": "Enter the 6-digit code from your authenticator app",
        }

    # ── 2FA not enabled: issue full token ─────────────
    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        username=user["username"],
    )
    logger.info(f"User logged in: {form_data.username}")

    return AuthResponse(
        access_token=access_token,
        user_id=user["id"],
        email=user["email"],
        username=user["username"],
    )


# ── 3. ENABLE 2FA ─────────────────────────────────────────────────────────────

@router.post("/enable-2fa", response_model=Enable2FAResponse)
async def enable_2fa(current_user: dict = Depends(get_current_user)) -> Enable2FAResponse:
    """
    Generate a TOTP secret, save it to DB, return QR code.
    User must scan QR with Google Authenticator.
    Requires: valid full access token (not temp token).
    """
    if current_user.get("is_2fa_enabled"):
        raise HTTPException(status_code=400, detail="2FA is already enabled")

    secret = _generate_totp_secret()
    await enable_user_2fa(current_user["id"], secret)

    uri = _get_totp_uri(secret, current_user["email"])
    qr_b64 = _generate_qr_base64(uri)

    logger.info(f"2FA enabled for: {current_user['email']}")
    return Enable2FAResponse(
        qr_code_url=f"data:image/png;base64,{qr_b64}",
        totp_secret=secret,
    )


# ── 4. VERIFY 2FA (complete login) ───────────────────────────────────────────

@router.post("/verify-2fa", response_model=AuthResponse)
async def verify_2fa(data: Verify2FARequest) -> AuthResponse:
    """
    Verify the OTP code using the temp_token from /login.
    Returns a full access token on success.
    """
    # Decode the temp token
    try:
        payload = decode_access_token(data.temp_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired temp token")

    # Must be a pending 2FA token
    if not payload.get("2fa_pending"):
        raise HTTPException(status_code=400, detail="Not a 2FA pending token")

    user = await get_user_by_id(payload.get("user_id"))
    if not user or not user.get("totp_secret"):
        raise HTTPException(status_code=404, detail="User not found or 2FA not set up")

    # Verify OTP
    if not _verify_totp(user["totp_secret"], data.otp_code):
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    # Issue full access token
    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        username=user["username"],
    )
    logger.info(f"2FA verified, full token issued: {user['email']}")

    return AuthResponse(
        access_token=access_token,
        user_id=user["id"],
        email=user["email"],
        username=user["username"],
    )


# ── 5. DISABLE 2FA ───────────────────────────────────────────────────────────

@router.post("/disable-2fa")
async def disable_2fa(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Disable 2FA and clear the TOTP secret.
    Requires: valid full access token.
    """
    if not current_user.get("is_2fa_enabled"):
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    await disable_user_2fa(current_user["id"])
    logger.info(f"2FA disabled for: {current_user['email']}")
    return {"message": "2FA disabled successfully"}


# ── 6. ME ─────────────────────────────────────────────────────────────────────

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)) -> dict:
    """Return the authenticated user's profile."""
    return {
        "user_id": current_user["id"],
        "email": current_user["email"],
        "username": current_user["username"],
        "created_at": current_user["created_at"],
        "is_2fa_enabled": current_user.get("is_2fa_enabled", False),
    }