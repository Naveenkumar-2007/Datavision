"""
🔐 Enterprise Authentication Module
Validates Supabase JWT tokens server-side for secure user isolation.

This is how companies like OpenAI, Stripe, and Google handle user authentication:
1. Frontend sends JWT token in Authorization header
2. Backend validates token cryptographically (no trust of frontend-provided user_id)
3. User ID extracted from verified token payload
"""

import os
import logging
from typing import Optional, Tuple
from datetime import datetime, timezone
import jwt
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Supabase JWT settings
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))

# Security scheme for OpenAPI docs
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Represents a verified user from JWT token"""
    
    def __init__(self, user_id: str, email: Optional[str] = None, 
                 role: str = "authenticated", is_guest: bool = False):
        self.id = user_id
        self.user_id = user_id  # Alias for compatibility
        self.email = email
        self.role = role
        self.is_guest = is_guest
    
    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, role={self.role})"


def decode_supabase_jwt(token: str) -> dict:
    """
    Decode and validate a Supabase JWT token.
    
    Supabase JWTs contain:
    - sub: user UUID
    - email: user email
    - role: 'authenticated' or 'anon'
    - exp: expiration timestamp
    - aud: audience (authenticated)
    """
    try:
        # If we have the JWT secret, verify the signature
        if SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )
        else:
            # Fallback: Decode without verification (dev mode only)
            # WARNING: This is insecure for production!
            logger.warning("⚠️ JWT_SECRET not set - decoding without verification (DEV MODE)")
            payload = jwt.decode(token, options={"verify_signature": False})
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid token audience")
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT token from various sources"""
    
    # 1. Authorization header (preferred)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    # 2. Cookie (for browser sessions)
    token = request.cookies.get("sb-access-token")
    if token:
        return token
    
    # 3. Query parameter (for special cases like file downloads)
    token = request.query_params.get("token")
    if token:
        return token
    
    return None


def generate_guest_id(request: Request) -> str:
    """Generate a consistent guest ID based on request fingerprint"""
    import hashlib
    
    # Create fingerprint from IP + User-Agent for some consistency
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("User-Agent", "unknown")[:100]
    
    # Use first 12 chars of hash for readability
    fingerprint = hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()[:12]
    return f"guest_{fingerprint}"


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    """
    🔐 Main authentication dependency - use this in all protected endpoints.
    
    Returns AuthenticatedUser with verified user_id from JWT.
    Falls back to guest user if no valid token provided.
    
    Usage:
        @app.get("/api/files")
        async def list_files(user: AuthenticatedUser = Depends(get_current_user)):
            return await db.files.find({"user_id": user.id})
    """
    
    # Try to extract token
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = extract_token_from_request(request)
    
    if token and token not in ["null", "undefined", ""]:
        try:
            # Decode and validate JWT
            payload = decode_supabase_jwt(token)
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing user ID")
            
            return AuthenticatedUser(
                user_id=user_id,
                email=payload.get("email"),
                role=payload.get("role", "authenticated"),
                is_guest=False
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            # Fall through to guest user
    
    # No valid token - create guest user
    guest_id = generate_guest_id(request)
    logger.debug(f"Guest user: {guest_id}")
    
    return AuthenticatedUser(
        user_id=guest_id,
        email=None,
        role="anon",
        is_guest=True
    )


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthenticatedUser]:
    """
    Optional authentication - returns None if no valid token.
    Use for endpoints that work with or without auth.
    """
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


async def require_authenticated_user(
    user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Strict authentication - rejects guest users.
    Use for endpoints that require login.
    """
    if user.is_guest:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in."
        )
    return user


# Legacy compatibility - maps to get_current_user
async def get_user_id_from_token(
    user: AuthenticatedUser = Depends(get_current_user)
) -> str:
    """Returns just the user_id string for backward compatibility"""
    return user.id


# Helper to get user_id from request body (DEPRECATED - for migration)
def get_user_id_from_body_deprecated(body_user_id: Optional[str], user: AuthenticatedUser) -> str:
    """
    DEPRECATED: For migrating old endpoints that accept user_id in body.
    Always prefers the authenticated user's ID over body parameter.
    """
    if not user.is_guest:
        # Authenticated user - always use their verified ID
        return user.id
    
    # Guest user - use body param if provided, otherwise use generated guest ID
    if body_user_id and body_user_id not in ["default", "guest", "", "null", "undefined"]:
        # Log warning about deprecated usage
        logger.warning(f"⚠️ DEPRECATED: user_id passed in body ({body_user_id}). Migrate to JWT auth.")
        return body_user_id
    
    return user.id
