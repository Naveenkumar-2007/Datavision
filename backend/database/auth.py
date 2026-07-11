import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.orm import UserProfile
from core.auth import create_access_token, verify_password, get_password_hash
from core.auth import get_current_user, get_current_user_optional, AuthenticatedUser as AuthUser, get_admin_user, get_super_admin_user, decode_jwt
from database.models import AuthSignUp, AuthLogin, AuthMagicLink, UserRole

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(self, email: str, password: str, metadata: dict = None) -> dict:
        metadata = metadata or {}
        stmt = select(UserProfile).where(UserProfile.email == email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            return {"success": False, "message": "Email already registered"}
        
        hashed_password = get_password_hash(password)
        new_user = UserProfile(
            email=email,
            hashed_password=hashed_password,
            full_name=metadata.get("full_name"),
            company_name=metadata.get("company_name")
        )
        self.db.add(new_user)
        try:
            await self.db.commit()
            await self.db.refresh(new_user)
        except Exception as e:
            await self.db.rollback()
            return {"success": False, "message": str(e)}

        access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email, "role": new_user.role})
        
        return {
            "success": True,
            "user": {"id": str(new_user.id), "email": new_user.email},
            "session": {"access_token": access_token},
            "message": "Signup successful"
        }

    async def login(self, email: str, password: str) -> dict:
        stmt = select(UserProfile).where(UserProfile.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return {"success": False, "message": "Invalid credentials"}
        
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
        
        return {
            "success": True,
            "user": {"id": str(user.id), "email": user.email},
            "session": {"access_token": access_token}
        }

    async def get_user_profile(self, user_id: str) -> dict:
        stmt = select(UserProfile).where(UserProfile.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return {
                "success": True, 
                "profile": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "company_name": user.company_name,
                    "avatar_url": user.avatar_url,
                    "role": user.role
                }
            }
        return {"success": False, "message": "User not found"}

    async def update_user_profile(self, user_id: str, updates: dict) -> dict:
        stmt = select(UserProfile).where(UserProfile.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return {"success": False, "message": "User not found"}
        
        for k, v in updates.items():
            if hasattr(user, k):
                setattr(user, k, v)
                
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return {
                "success": True, 
                "profile": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "company_name": user.company_name,
                    "avatar_url": user.avatar_url,
                    "role": user.role
                }
            }
        except Exception as e:
            await self.db.rollback()
            return {"success": False, "message": str(e)}
            
    async def logout(self, token: str) -> dict:
        return {"success": True, "message": "Logged out successfully"}
        
    async def refresh_token(self, token: str) -> dict:
        return {"success": False, "message": "Refresh tokens require implementation"}

    async def send_magic_link(self, email: str) -> dict:
        return {"success": False, "message": "Magic link not supported natively yet"}

    async def update_or_create_oauth_user(self, provider: str, email: str, full_name: str = None) -> dict:
        stmt = select(UserProfile).where(UserProfile.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            import secrets
            random_password = secrets.token_urlsafe(32)
            hashed_password = get_password_hash(random_password)
            user = UserProfile(
                email=email,
                hashed_password=hashed_password,
                full_name=full_name
            )
            self.db.add(user)
            try:
                await self.db.commit()
                await self.db.refresh(user)
            except Exception as e:
                await self.db.rollback()
                return {"success": False, "message": str(e)}
        
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
        
        return {
            "success": True,
            "user": {"id": str(user.id), "email": user.email},
            "session": {"access_token": access_token}
        }

def get_auth_service(db: AsyncSession) -> AuthService:
    return AuthService(db)

async def get_user_id_from_headers(x_user_id: Optional[str] = None, authorization: Optional[str] = None) -> str:
    # 1. First, always prioritize the Authorization header for absolute security.
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
                            print(f"❌ Developer Token Revoked: {token}")
                            return "default"
                        key.total_calls += 1
                        await db.commit()
                        print(f"✅ Developer Token Auth Success for user: {key.user_id}")
                        return str(key.user_id)
                    else:
                        print(f"❌ Developer Token not found in DB: {token}")
            except Exception as e:
                print(f"💥 Developer Token Auth Error: {e}")
                
        # Otherwise, decode as JWT
        else:
            try:
                payload = decode_jwt(token)
                return payload.get("sub", "default")
            except Exception as e:
                print(f"💥 JWT Decode Error: {e}")

    # 2. Fallback to X-User-ID for guests and legacy endpoints.
    if x_user_id and x_user_id not in ["default", "guest", "", "null", "undefined"]:
        print(f"⚠️ Falling back to X-User-ID: {x_user_id}")
        return x_user_id

    print("⚠️ Falling back to 'default'")
    return "default"
