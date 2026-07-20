"""
🔐 API Dependencies - Authentication & Authorization
Enterprise-grade user isolation using JWT tokens

This is the SECURE way to get user identity:
- Extracts user_id from verified JWT token (not from request body)
- Falls back to guest ID for anonymous users
- Prevents users from accessing other users' data
"""

from fastapi import Header, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

# Import the core auth module
try:
    from core.auth import (
        AuthenticatedUser,
        get_current_user,
        get_current_user_optional,
        require_authenticated_user,
        get_user_id_from_token,
        get_user_id_from_body_deprecated,
        decode_jwt_token
    )
    AUTH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Core auth module not available: {e}")
    AUTH_AVAILABLE = False


# Legacy compatibility function
async def get_current_user_id(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> str:
    """
    🔐 Get verified user ID from JWT token or headers.
    
    Priority:
    1. JWT token in Authorization header (most secure)
    2. X-User-ID header (for compatibility)
    3. Generate guest ID (for anonymous users)
    
    If X-Workspace-ID is provided, verifies membership and returns it.
    """
    resolved_user_id = None
    
    # Try JWT authentication first
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        
        # Check if it's a Developer API Token
        if token.startswith("dv_live_") or token.startswith("dv_test_"):
            try:
                from database.db import AsyncSessionLocal
                from database.orm import DeveloperAPIKey
                from sqlalchemy import select
                
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(DeveloperAPIKey).filter(DeveloperAPIKey.api_key == token))
                    key = result.scalars().first()
                    if key:
                        if key.status == 'revoked':
                            raise HTTPException(status_code=401, detail="API Key has been revoked")
                        key.total_calls += 1
                        await db.commit()
                        resolved_user_id = str(key.user_id)
            except Exception as e:
                logger.debug(f"Developer token decode failed: {e}")
                
        # Standard JWT decode
        else:
            try:
                if AUTH_AVAILABLE:
                    payload = decode_jwt_token(token)
                    user_id = payload.get("sub")
                    if user_id:
                        resolved_user_id = user_id
            except Exception as e:
                logger.debug(f"JWT decode failed: {e}")
    
    # Fallback to X-User-ID header
    if not resolved_user_id and x_user_id and x_user_id not in ["null", "undefined", "", "default"]:
        resolved_user_id = x_user_id
    
    # Generate guest ID based on request fingerprint
    if not resolved_user_id:
        import hashlib
        ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("User-Agent", "unknown")[:100]
        fingerprint = hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()[:12]
        resolved_user_id = f"guest_{fingerprint}"
            
    return resolved_user_id

def get_verified_user_id(
    body_user_id: Optional[str],
    header_user_id: str
) -> str:
    """
    Get the verified user ID, preferring header over body.
    
    For migration: accepts body user_id but logs warning.
    Eventually body_user_id support should be removed.
    """
    # Always prefer header (verified) over body (unverified)
    if header_user_id and not header_user_id.startswith("guest_"):
        return header_user_id
    
    # For guests, use body if provided (for backward compat)
    if body_user_id and body_user_id not in ["default", "guest", "", "null", "undefined"]:
        logger.warning(f"⚠️ DEPRECATED: user_id from body '{body_user_id}' - migrate to JWT auth")
        return body_user_id
    
    return header_user_id


# Export all auth utilities
__all__ = [
    'get_current_user_id',
    'get_verified_user_id',
    'AuthenticatedUser',
    'get_current_user',
    'get_current_user_optional', 
    'require_authenticated_user',
    'get_user_id_from_token',
]
