from uuid import uuid4
from datetime import datetime, timedelta, timezone

import pyotp
import qrcode
import io
import base64

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError

from src.config.database import (
    create_user,
    create_backup_codes,
    create_refresh_token,
    create_reset_token,
    delete_backup_codes,
    find_and_consume_backup_code,
    get_refresh_token,
    get_reset_token,
    get_unused_backup_codes_count,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    mark_reset_token_used,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    update_user_password,
    enable_user_2fa,
    disable_user_2fa,
)
from src.config.settings import settings
from src.utils.auth import (
    create_access_token,
    generate_backup_codes,
    generate_refresh_token,
    generate_reset_token,
    hash_backup_code,
    hash_password,
    hash_reset_token,
    hash_refresh_token,
    verify_password,
    decode_access_token,
)
from src.utils.auth_deps import get_current_user
from src.utils.logger import logger
from src.utils.rate_limit import limiter

router = APIRouter()
bearer_scheme = HTTPBearer()


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


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
@limiter.limit("3/minute")
async def register_user(request: Request, payload: RegisterRequest) -> AuthResponse:
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
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    raw_refresh_token, refresh_hash = generate_refresh_token()
    refresh_expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    await create_refresh_token(
        token_id=str(uuid4()),
        user_id=user_id,
        token_hash=refresh_hash,
        expires_at=refresh_expires_at,
    )
    logger.info(f"New user registered: {payload.email}")

    return AuthResponse(
        access_token=access_token,
        refresh_token=raw_refresh_token,
        user_id=user_id,
        email=payload.email,
        username=payload.username,
    )


# ── 2. LOGIN ──────────────────────────────────────────────────────────────────

@router.post("/login")
@limiter.limit("5/minute")
async def login_user(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
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
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    raw_refresh_token, refresh_hash = generate_refresh_token()
    refresh_expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    await create_refresh_token(
        token_id=str(uuid4()),
        user_id=user["id"],
        token_hash=refresh_hash,
        expires_at=refresh_expires_at,
    )
    logger.info(f"User logged in: {form_data.username}")

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "user_id": user["id"],
        "email": user["email"],
        "username": user["username"],
    }


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

@router.post("/verify-2fa")
@limiter.limit("5/minute")
async def verify_2fa(request: Request, data: Verify2FARequest) -> dict:
    """
    Verify the OTP code using the provided token.
    Accepts a 2FA-pending token on login, or the user's live access token during setup confirmation.
    """
    # Decode the token (login temp token or live access token during setup)
    try:
        payload = decode_access_token(data.temp_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired temp token")

    is_setup_confirmation = not bool(payload.get("2fa_pending"))
    user = await get_user_by_id(payload.get("user_id"))
    if not user or not user.get("totp_secret"):
        raise HTTPException(status_code=404, detail="User not found or 2FA not set up")

    # Verify OTP; if not valid, also allow backup code consumption.
    is_backup_code = False
    if _verify_totp(user["totp_secret"], data.otp_code):
        valid = True
    else:
        is_backup_code = await find_and_consume_backup_code(
            user["id"],
            hash_backup_code(data.otp_code),
        )
        valid = bool(is_backup_code)

    if not valid:
        raise HTTPException(status_code=401, detail="Invalid OTP code")

    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        username=user["username"],
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    raw_refresh_token, refresh_hash = generate_refresh_token()
    refresh_expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    await create_refresh_token(
        token_id=str(uuid4()),
        user_id=user["id"],
        token_hash=refresh_hash,
        expires_at=refresh_expires_at,
    )

    response = {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "user_id": user["id"],
        "email": user["email"],
        "username": user["username"],
    }

    if is_setup_confirmation:
        existing_backup_count = await get_unused_backup_codes_count(user["id"])
        if existing_backup_count == 0:
            raw_backup_codes = generate_backup_codes()
            hashed_codes = [hash_backup_code(code) for code in raw_backup_codes]
            await create_backup_codes(user["id"], hashed_codes)
            # Shown once and never retrievable again.
            response["backup_codes"] = raw_backup_codes

    logger.info(f"2FA verified, full token issued: {user['email']}")
    return response


@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh_token(request: Request, payload: RefreshRequest) -> dict:
    """Rotate refresh tokens and issue a new access token."""
    token_hash = hash_refresh_token(payload.refresh_token)
    row = await get_refresh_token(token_hash)
    if not row:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    await revoke_refresh_token(row["id"])
    user = await get_user_by_id(row["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        username=user["username"],
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    raw_refresh_token, refresh_hash = generate_refresh_token()
    refresh_expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    await create_refresh_token(
        token_id=str(uuid4()),
        user_id=user["id"],
        token_hash=refresh_hash,
        expires_at=refresh_expires_at,
    )

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "user_id": user["id"],
        "email": user["email"],
        "username": user["username"],
    }


@router.post("/logout")
async def logout(request: Request, payload: LogoutRequest) -> dict:
    """Revoke the provided refresh token and return success."""
    token_hash = hash_refresh_token(payload.refresh_token)
    row = await get_refresh_token(token_hash)
    if row:
        await revoke_refresh_token(row["id"])
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest) -> dict:
    """Begin password reset flow without leaking whether the email exists."""
    user = await get_user_by_email(payload.email)
    if not user:
        return {"message": "If that email exists, a reset link has been generated"}

    raw_token, token_hash = generate_reset_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    await create_reset_token(
        token_id=str(uuid4()),
        user_id=user["id"],
        token_hash=token_hash,
        expires_at=expires_at,
    )
    # In production this would be emailed and the raw token would never be returned.
    return {
        "message": "Reset token generated (dev mode — no email configured)",
        "reset_token": raw_token,
        "expires_in_minutes": 30,
    }


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, payload: ResetPasswordRequest) -> dict:
    """Complete password reset when the user provides a valid reset token."""
    token_hash = hash_reset_token(payload.token)
    row = await get_reset_token(token_hash)
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    new_hashed = hash_password(payload.new_password)
    await update_user_password(row["user_id"], new_hashed)
    await revoke_all_user_refresh_tokens(row["user_id"])
    await mark_reset_token_used(row["id"])

    return {"message": "Password has been reset successfully"}


# ── 5. DISABLE 2FA ───────────────────────────────────────────────────────────

@router.post("/regenerate-backup-codes")
@limiter.limit("3/hour")
async def regenerate_backup_codes(request: Request, current_user: dict = Depends(get_current_user)) -> dict:
    """Generate a fresh set of backup codes for the authenticated user."""
    if not current_user.get("is_2fa_enabled"):
        raise HTTPException(status_code=400, detail="2FA must be enabled to regenerate backup codes")

    raw_backup_codes = generate_backup_codes()
    hashed_codes = [hash_backup_code(code) for code in raw_backup_codes]
    await create_backup_codes(current_user["id"], hashed_codes)

    return {"backup_codes": raw_backup_codes}


@router.post("/disable-2fa")
async def disable_2fa(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Disable 2FA and clear the TOTP secret.
    Requires: valid full access token.
    """
    if not current_user.get("is_2fa_enabled"):
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    await disable_user_2fa(current_user["id"])
    await delete_backup_codes(current_user["id"])
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