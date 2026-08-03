"""
Auth API Endpoints — /api/v2/auth/*

Production-grade authentication with token rotation and session management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.auth_service import AuthService
from app.core.permissions import get_current_user, AuthenticatedUser
from app.schemas.auth import (
    SignUpRequest,
    LoginRequest,
    RefreshTokenRequest,
    MagicLinkRequest,
    ChangePasswordRequest,
    AuthResponse,
    TokenPair,
    SessionInfo,
)
from app.schemas.common import MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_info(request: Request) -> tuple[str | None, str | None]:
    """Extract IP and user agent from request."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")
    return ip, ua


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: Request,
    body: SignUpRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    ip, ua = _get_client_info(request)
    service = AuthService(db)

    try:
        return await service.register(body, ip_address=ip, user_agent=ua)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and receive access + refresh tokens."""
    ip, ua = _get_client_info(request)
    service = AuthService(db)

    try:
        return await service.login(body, ip_address=ip, user_agent=ua)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and get a new access + refresh token pair."""
    ip, _ = _get_client_info(request)
    service = AuthService(db)

    try:
        return await service.refresh_tokens(body.refresh_token, ip_address=ip)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout(
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current session."""
    service = AuthService(db)
    await service.logout(user.id)
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all sessions — logout from all devices."""
    service = AuthService(db)
    await service.logout_all(user.id)
    return MessageResponse(message="All sessions revoked")


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active sessions for the current user."""
    service = AuthService(db)
    return await service.get_active_sessions(user.id)


@router.get("/me", response_model=dict)
async def get_current_user_info(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get current authenticated user info from token."""
    return {
        "id": user.id,
        "email": user.email,
        "roles": user.roles,
        "highest_role": user.highest_role,
    }
