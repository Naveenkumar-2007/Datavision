"""
Authentication Endpoints
Handles signup, login, logout, OAuth, and magic link authentication
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional

from database import (
    get_auth_service,
    get_current_user,
    get_current_user_optional,
    AuthUser,
    AuthSignUp,
    AuthLogin,
    AuthMagicLink
)

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class MagicLinkRequest(BaseModel):
    email: str


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthRequest(BaseModel):
    redirect_to: Optional[str] = None


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@router.post("/signup")
async def signup(request: SignupRequest):
    """
    Create a new user account with email and password.
    Supabase sends confirmation email via configured SMTP (Resend).
    """
    auth_service = get_auth_service()
    
    metadata = {}
    if request.full_name:
        metadata["full_name"] = request.full_name
    if request.company_name:
        metadata["company_name"] = request.company_name
    
    result = await auth_service.signup(
        email=request.email,
        password=request.password,
        metadata=metadata
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Signup failed"))
    
    return {
        "success": True,
        "user": result.get("user"),
        "session": result.get("session"),
        "message": "Account created! Please check your inbox to confirm your email."
    }


@router.get("/confirm-email")
async def confirm_email(token: str):
    """
    Verify email confirmation token and mark user as verified.
    Called when user clicks the confirmation link in email.
    """
    from services.confirmation_email import verify_confirmation_token
    
    result = await verify_confirmation_token(token)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Invalid token"))
    
    # Token is valid - user email is confirmed
    return {
        "success": True,
        "message": "Email confirmed successfully! You can now log in.",
        "email": result.get("email"),
        "redirect": "/login"
    }


@router.post("/login")
async def login(request: LoginRequest):
    """
    Login with email and password.
    Returns access token and user info.
    """
    auth_service = get_auth_service()
    
    result = await auth_service.login(
        email=request.email,
        password=request.password
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("message", "Invalid credentials"))
    
    return {
        "success": True,
        "user": result.get("user"),
        "session": result.get("session")
    }


@router.post("/logout")
async def logout(current_user: AuthUser = Depends(get_current_user)):
    """
    Logout current user and invalidate session.
    """
    auth_service = get_auth_service()
    result = await auth_service.logout("")
    
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.post("/magic-link")
async def send_magic_link(request: MagicLinkRequest):
    """
    Send a magic link to the user's email for passwordless login.
    """
    auth_service = get_auth_service()
    
    result = await auth_service.send_magic_link(request.email)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to send magic link"))
    
    return {
        "success": True,
        "message": f"Magic link sent to {request.email}. Check your inbox!"
    }


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    auth_service = get_auth_service()
    
    result = await auth_service.refresh_token(request.refresh_token)
    
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("message", "Token refresh failed"))
    
    return {
        "success": True,
        "session": result.get("session")
    }


@router.get("/oauth/{provider}")
async def get_oauth_url(provider: str, redirect_to: Optional[str] = None):
    """
    Get OAuth URL for social login.
    Supported providers: google, github
    """
    if provider not in ["google", "github"]:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    auth_service = get_auth_service()
    
    result = await auth_service.get_oauth_url(provider, redirect_to)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to get OAuth URL"))
    
    return {
        "success": True,
        "provider": provider,
        "url": result.get("url")
    }


@router.get("/me")
async def get_current_user_info(current_user: AuthUser = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    """
    auth_service = get_auth_service()
    
    # Get full profile from database
    result = await auth_service.get_user_profile(current_user.id)
    
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role.value,
            "is_admin": current_user.is_admin,
            "profile": result.get("profile") if result.get("success") else None
        }
    }


@router.put("/profile")
async def update_profile(
    updates: dict,
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Update current user's profile.
    """
    # Only allow certain fields to be updated
    allowed_fields = {"full_name", "avatar_url", "company_name"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    auth_service = get_auth_service()
    result = await auth_service.update_user_profile(current_user.id, filtered_updates)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Update failed"))
    
    return {
        "success": True,
        "profile": result.get("profile"),
        "message": "Profile updated successfully"
    }


@router.get("/check")
async def check_auth(current_user: Optional[AuthUser] = Depends(get_current_user_optional)):
    """
    Check if user is authenticated.
    Returns user info if authenticated, null if not.
    """
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "role": current_user.role.value,
                "is_admin": current_user.is_admin
            }
        }
    else:
        return {
            "authenticated": False,
            "user": None
        }
