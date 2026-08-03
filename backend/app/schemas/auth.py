"""
Auth Schemas — Pydantic v2 request/response models for authentication.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ─────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    """Registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class MagicLinkRequest(BaseModel):
    """Magic link request."""
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Request a password reset."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm a password reset with the token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Change password for authenticated user."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Response Schemas ────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Public user profile response."""
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    company_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    roles: list[str] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    """Access + refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class AuthResponse(BaseModel):
    """Full auth response (login/signup)."""
    user: UserResponse
    session: TokenPair
    message: str = "Success"


class SessionInfo(BaseModel):
    """Information about an active session."""
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_current: bool = False

    model_config = {"from_attributes": True}
