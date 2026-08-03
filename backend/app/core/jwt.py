"""
JWT Module — Access and refresh token creation, validation, and revocation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Literal

from jose import jwt, JWTError
from fastapi import HTTPException, status

from app.core.config import get_settings


def create_access_token(
    user_id: str,
    email: str,
    roles: list[str] | None = None,
    extra_claims: dict | None = None,
) -> str:
    """
    Create a short-lived access token (default 30 minutes).
    Contains user identity and role information.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "email": email,
        "roles": roles or [],
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    session_id: str,
    family_id: str | None = None,
) -> tuple[str, datetime]:
    """
    Create a long-lived refresh token (default 7 days).
    Returns (token_string, expires_at).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "session_id": session_id,
        "family_id": family_id or session_id,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expire


def decode_token(
    token: str,
    expected_type: Literal["access", "refresh"] | None = None,
) -> dict:
    """
    Decode and validate a JWT token.
    Raises HTTPException on invalid/expired tokens.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token type if specified
    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Expected {expected_type} token, got {payload.get('type')}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def decode_token_no_exception(token: str) -> Optional[dict]:
    """Decode a token without raising exceptions. Returns None on failure."""
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None
