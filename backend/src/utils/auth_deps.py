from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from src.config.database import get_user_by_id
from src.utils.auth import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency that verifies the JWT token and returns the current user.
    Uses HTTPBearer so Swagger shows a clean token input box instead of
    username/password form.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials  # strips "Bearer " automatically
        payload = decode_token(token)

        # Block temp tokens (2FA not completed yet)
        if payload.get("2fa_pending"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Complete 2FA verification first",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Try user_id first, fall back to sub for backward compatibility
        user_id: str = payload.get("user_id") or payload.get("sub")
        if not user_id:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(user_id)
    if not user:
        raise credentials_exception

    return user