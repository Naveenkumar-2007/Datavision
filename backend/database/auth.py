"""
Authentication Helpers
JWT verification and user authentication utilities
"""

import os
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, Header, Depends, Request
from jose import jwt, JWTError
from functools import wraps

from database.supabase_client import get_supabase_client, get_supabase_admin_client
from database.models import AuthUser, UserRole

# Supabase JWT secret (get from Supabase Dashboard -> Settings -> API -> JWT Secret)
# SECURITY: Never fall back to service role key - it has elevated privileges
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
JWT_ALGORITHM = "HS256"

if not JWT_SECRET:
    import logging
    logging.getLogger("auth").warning(
        "⚠️ SUPABASE_JWT_SECRET not configured! JWT verification will fail. "
        "Get this from Supabase Dashboard -> Settings -> API -> JWT Secret"
    )


def decode_jwt(token: str) -> dict:
    """
    Decode and verify a Supabase JWT token.
    Returns the payload if valid, raises exception otherwise.
    """
    try:
        # Supabase JWTs are signed with the JWT secret
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience="authenticated"
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_user_id_from_headers(
    x_user_id: Optional[str] = None,
    authorization: Optional[str] = None,
    require_auth: bool = False
) -> Optional[str]:
    """
    Extract user ID from JWT token or X-User-ID header.
    Works for both authenticated and legacy/demo sessions.
    
    SECURITY: Set require_auth=True for sensitive operations.
    """
    user_id = None
    
    # Try JWT token first (most secure)
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            payload = decode_jwt(token)
            user_id = payload.get("sub")
            print(f"🔐 Auth - User from JWT: {user_id}")
        except Exception as e:
            print(f"⚠️ JWT decode error: {e}")
            if require_auth:
                raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Fallback to X-User-ID header (only if explicitly provided)
    if not user_id and x_user_id:
        # SECURITY: Validate the user_id format
        import re
        if re.match(r'^[a-zA-Z0-9_-]+$', x_user_id) and '..' not in x_user_id:
            user_id = x_user_id
            print(f"🔐 Auth - User from header: {user_id}")
        else:
            print(f"⚠️ Invalid X-User-ID format: {x_user_id}")
    
    if not user_id:
        if require_auth:
            raise HTTPException(status_code=401, detail="Authentication required")
        # SECURITY: Return None instead of default user - let caller decide
        return None
    
    return user_id


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> AuthUser:
    """
    Dependency to get current authenticated user from JWT.
    Raises 401 if not authenticated.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    # Decode JWT
    payload = decode_jwt(token)
    
    # Extract user info
    user_id = payload.get("sub")
    email = payload.get("email", "")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Get user role from database
    try:
        client = get_supabase_admin_client()
        result = client.table("profiles").select("role").eq("id", user_id).single().execute()
        role = result.data.get("role", "user") if result.data else "user"
    except Exception:
        role = "user"
    
    return AuthUser(
        id=user_id,
        email=email,
        role=UserRole(role),
        is_admin=role in ["admin", "super_admin"]
    )


async def get_current_user_optional(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Optional[AuthUser]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Does not raise exception if not authenticated.
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


async def get_admin_user(
    current_user: AuthUser = Depends(get_current_user)
) -> AuthUser:
    """
    Dependency to ensure current user is an admin.
    Raises 403 if not admin.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_super_admin_user(
    current_user: AuthUser = Depends(get_current_user)
) -> AuthUser:
    """
    Dependency to ensure current user is a super admin.
    Raises 403 if not super admin.
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check for authorization header in request
        request = kwargs.get('request')
        if request:
            auth_header = request.headers.get('authorization')
            if not auth_header:
                raise HTTPException(status_code=401, detail="Not authenticated")
        return await func(*args, **kwargs)
    return wrapper


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.admin_client = get_supabase_admin_client()
    
    async def signup(self, email: str, password: str, metadata: dict = None) -> dict:
        """
        Sign up a new user with email and password.
        """
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })
            
            if response.user:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email
                    },
                    "session": {
                        "access_token": response.session.access_token if response.session else None,
                        "refresh_token": response.session.refresh_token if response.session else None
                    },
                    "message": "Signup successful" if response.session else "Please check your email to confirm your account"
                }
            else:
                return {"success": False, "message": "Signup failed"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def login(self, email: str, password: str) -> dict:
        """
        Login with email and password.
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email
                    },
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at
                    }
                }
            else:
                return {"success": False, "message": "Login failed"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def logout(self, access_token: str) -> dict:
        """
        Logout user and invalidate session.
        """
        try:
            self.client.auth.sign_out()
            return {"success": True, "message": "Logged out successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def send_magic_link(self, email: str) -> dict:
        """
        Send magic link for passwordless login.
        """
        try:
            response = self.client.auth.sign_in_with_otp({
                "email": email
            })
            return {
                "success": True,
                "message": f"Magic link sent to {email}"
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)
            
            if response.session:
                return {
                    "success": True,
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at
                    }
                }
            else:
                return {"success": False, "message": "Token refresh failed"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def get_oauth_url(self, provider: str, redirect_to: str = None) -> dict:
        """
        Get OAuth URL for social login.
        Supported providers: google, github
        """
        try:
            response = self.client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirect_to": redirect_to or "http://localhost:5173/auth/callback"
                }
            })
            return {
                "success": True,
                "url": response.url
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def get_user_profile(self, user_id: str) -> dict:
        """
        Get user profile from database.
        """
        try:
            result = self.admin_client.table("profiles").select("*").eq("id", user_id).single().execute()
            return {"success": True, "profile": result.data}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def update_user_profile(self, user_id: str, updates: dict) -> dict:
        """
        Update user profile.
        """
        try:
            result = self.admin_client.table("profiles").update(updates).eq("id", user_id).execute()
            return {"success": True, "profile": result.data[0] if result.data else None}
        except Exception as e:
            return {"success": False, "message": str(e)}


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get auth service singleton"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
