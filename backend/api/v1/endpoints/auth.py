"""
Authentication Endpoints
Handles signup, login, logout, OAuth, and magic link authentication
"""

import re
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from database.db import get_db
from database import (
    get_auth_service,
    get_current_user,
    get_current_user_optional,
    AuthUser
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
    
    @classmethod
    def validate_password_strength(cls, password: str) -> None:
        """Validate password meets security requirements"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(password) > 128:
            raise ValueError("Password must be less than 128 characters")
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password):
            raise ValueError("Password must contain at least one number")
        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein']
        if password.lower() in weak_passwords:
            raise ValueError("Password is too common. Please choose a stronger password")


class LoginRequest(BaseModel):
    email: str
    password: str


class MagicLinkRequest(BaseModel):
    email: str

class AcceptInviteRequest(BaseModel):
    token: str
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthRequest(BaseModel):
    redirect_to: Optional[str] = None


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@router.post("/signup")
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account with email and password.
    """
    try:
        SignupRequest.validate_password_strength(request.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(request.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    auth_service = get_auth_service(db)
    
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
        "message": "Account created successfully!"
    }


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.
    Returns access token and user info.
    """
    auth_service = get_auth_service(db)
    
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


@router.post("/accept-invite")
async def accept_invite(request: AcceptInviteRequest, db: AsyncSession = Depends(get_db)):
    """Accept an invitation by setting a password."""
    try:
        from core.auth import decode_jwt_token, get_password_hash
        from sqlalchemy import select
        from database.orm import UserProfile
        
        payload = decode_jwt_token(request.token)
        if payload.get("type") != "invite" or payload.get("email") != request.email:
            raise HTTPException(status_code=400, detail="Invalid or expired invite token")
            
        user_stmt = select(UserProfile).filter(UserProfile.email == request.email)
        user_res = await db.execute(user_stmt)
        target_user = user_res.scalars().first()
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        target_user.hashed_password = get_password_hash(request.password)
        await db.commit()
        
        return {"success": True, "message": "Password set successfully. You can now log in."}
    except Exception as e:
        logger.error(f"Failed to accept invite: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/logout")
async def logout(current_user: AuthUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Logout current user and invalidate session.
    """
    auth_service = get_auth_service(db)
    result = await auth_service.logout("")
    
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.post("/magic-link")
async def send_magic_link(request: MagicLinkRequest, db: AsyncSession = Depends(get_db)):
    auth_service = get_auth_service(db)
    result = await auth_service.send_magic_link(request.email)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to send magic link"))
    
    return {
        "success": True,
        "message": f"Magic link sent to {request.email}. Check your inbox!"
    }


@router.post("/refresh")
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    auth_service = get_auth_service(db)
    result = await auth_service.refresh_token(request.refresh_token)
    
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("message", "Token refresh failed"))
    
    return {
        "success": True,
        "session": result.get("session")
    }


@router.get("/oauth/{provider}")
async def login_via_oauth(provider: str, request: Request):
    if provider not in ["google", "github"]:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    from core.auth import oauth
    import os
    from fastapi.responses import RedirectResponse
    
    # Check if credentials are configured
    client_id = os.environ.get(f"{provider.upper()}_CLIENT_ID")
    if not client_id:
        frontend_url = os.environ.get("FRONTEND_URL", os.environ.get("APP_URL", "https://datavision-ai-datavision.hf.space"))
        return RedirectResponse(f"{frontend_url}/login?error={provider}_not_configured")
    
    try:
        space_host = os.environ.get("SPACE_HOST")
        if space_host:
            frontend_url = f"https://{space_host}"
        else:
            frontend_url = os.environ.get("FRONTEND_URL", os.environ.get("APP_URL", "http://localhost:5173"))
        
        redirect_uri_str = f"{frontend_url}/api/v1/auth/oauth/{provider}/callback"
        logger.info(f"OAuth {provider} redirect_uri: {redirect_uri_str}")
        
        client = oauth.create_client(provider)
        return await client.authorize_redirect(request, redirect_uri_str)
    except Exception as e:
        logger.error(f"OAuth redirect failed for {provider}: {e}")
        frontend_url = os.environ.get("FRONTEND_URL", os.environ.get("APP_URL", "https://datavision-ai-datavision.hf.space"))
        return RedirectResponse(f"{frontend_url}/login?error=oauth_failed")


@router.get("/oauth/{provider}/callback")
async def auth_via_oauth_callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    if provider not in ["google", "github"]:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    from core.auth import oauth
    import os
    from fastapi.responses import RedirectResponse
    
    client = oauth.create_client(provider)
    try:
        token = await client.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth login failed: {str(e)}")
    
    email = None
    full_name = None
    
    if provider == 'google':
        user_info = token.get('userinfo')
        if not user_info:
            resp = await client.get('https://openidconnect.googleapis.com/v1/userinfo', token=token)
            user_info = resp.json()
        email = user_info.get('email')
        full_name = user_info.get('name')
    elif provider == 'github':
        resp = await client.get('user', token=token)
        profile = resp.json()
        
        email_resp = await client.get('user/emails', token=token)
        emails = email_resp.json()
        email = next((e['email'] for e in emails if e.get('primary')), None)
        if not email and len(emails) > 0:
            email = emails[0]['email']
        
        full_name = profile.get('name') or profile.get('login')
    
    if not email:
        raise HTTPException(status_code=400, detail="Failed to retrieve email from OAuth provider")
        
    auth_service = get_auth_service(db)
    result = await auth_service.update_or_create_oauth_user(provider, email, full_name)
    
    if result.get("success"):
        access_token = result["session"]["access_token"]
        space_host = os.environ.get("SPACE_HOST")
        if space_host:
            frontend_url = f"https://{space_host}"
        else:
            frontend_url = os.environ.get("FRONTEND_URL", os.environ.get("APP_URL", "http://localhost:5173"))
        return RedirectResponse(f"{frontend_url}/auth/callback?token={access_token}")
        
    raise HTTPException(status_code=400, detail="Failed to process OAuth login")


@router.get("/me")
async def get_current_user_info(current_user: AuthUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Get current authenticated user's information.
    """
    auth_service = get_auth_service(db)
    result = await auth_service.get_user_profile(current_user.id)
    
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": getattr(current_user.role, 'value', current_user.role),
            "profile": result.get("profile") if result.get("success") else None
        }
    }


@router.put("/profile")
async def update_profile(
    updates: dict,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_fields = {"full_name", "avatar_url", "company_name"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    auth_service = get_auth_service(db)
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
    """
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "role": getattr(current_user.role, 'value', current_user.role)
            }
        }
    else:
        return {
            "authenticated": False,
            "user": None
        }
