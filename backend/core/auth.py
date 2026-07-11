import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import uuid
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

logger = logging.getLogger(__name__)

# Setup Authlib OAuth
oauth_config = Config(".env")
oauth = OAuth(oauth_config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

oauth.register(
    name='github',
    api_base_url='https://api.github.com/',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    client_kwargs={
        'scope': 'user:email'
    }
)

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days for ease of use

import bcrypt

security = HTTPBearer(auto_error=False)

class AuthenticatedUser:
    def __init__(self, user_id: str, email: Optional[str] = None, role: str = "authenticated", is_guest: bool = False):
        self.id = user_id
        self.user_id = user_id
        self.email = email
        self.role = role
        self.is_guest = is_guest

    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, role={self.role})"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token. Standard HS256 verification."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Backward-compatible aliases
decode_supabase_jwt = decode_jwt_token  # Deprecated: use decode_jwt_token

def decode_jwt(token: str) -> dict:
    return decode_jwt_token(token)

def extract_token_from_request(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.cookies.get("dv-access-token") or request.query_params.get("token")

def generate_guest_id(request: Request) -> str:
    import hashlib
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("User-Agent", "unknown")[:100]
    fingerprint = hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()[:12]
    return f"guest_{fingerprint}"

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthenticatedUser:
    token = credentials.credentials if credentials else extract_token_from_request(request)
    
    if token and token not in ["null", "undefined", ""]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing user ID")
            
            return AuthenticatedUser(
                user_id=user_id,
                email=payload.get("email"),
                role=payload.get("role", "authenticated"),
                is_guest=False
            )
        except JWTError as e:
            logger.warning(f"Token validation failed: {e}")
    
    guest_id = generate_guest_id(request)
    return AuthenticatedUser(user_id=guest_id, email=None, role="anon", is_guest=True)

async def get_current_user_optional(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None

async def require_authenticated_user(user: AuthenticatedUser = Depends(get_current_user)):
    if user.is_guest:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def get_user_id_from_token(user: AuthenticatedUser = Depends(get_current_user)) -> str:
    return user.id

def get_user_id_from_body_deprecated(body_user_id: Optional[str], user: AuthenticatedUser) -> str:
    if not user.is_guest:
        return user.id
    if body_user_id and body_user_id not in ["default", "guest", "", "null", "undefined"]:
        return body_user_id
    return user.id

async def get_admin_user(user: AuthenticatedUser = Depends(require_authenticated_user)):
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def get_super_admin_user(user: AuthenticatedUser = Depends(require_authenticated_user)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user
