"""
Auth Service — Core authentication business logic.

Handles registration, login, token refresh, logout, and session management.
All database operations are encapsulated here, keeping routes thin.
"""

import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    needs_rehash,
    validate_password_strength,
    generate_token,
    hash_token,
)
from app.core.jwt import create_access_token, create_refresh_token
from app.core.config import get_settings
from app.models.user import User, UserPreferences
from app.models.auth import UserSession, RefreshToken
from app.models.rbac import Role, UserRole
from app.schemas.auth import (
    SignUpRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    TokenPair,
    SessionInfo,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Encapsulates all authentication and session management logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Registration ────────────────────────────────────────────────

    async def register(
        self,
        request: SignUpRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResponse:
        """Register a new user, create default preferences and session."""

        # Check if email already exists
        existing = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("An account with this email already exists")

        # Validate password strength
        error = validate_password_strength(request.password)
        if error:
            raise ValueError(error)

        # Create user
        hashed, algorithm = hash_password(request.password)
        user = User(
            email=request.email,
            hashed_password=hashed,
            password_hash_algorithm=algorithm,
            full_name=request.full_name,
            company_name=request.company_name,
            is_active=True,
            is_verified=False,
            login_count=1,
            last_login_at=datetime.now(timezone.utc),
        )
        self.db.add(user)
        await self.db.flush()

        # Create default preferences
        preferences = UserPreferences(user_id=user.id)
        self.db.add(preferences)

        # Assign default role (viewer)
        default_role = await self._get_or_create_default_role()
        user_role = UserRole(
            user_id=user.id,
            role_id=default_role.id,
            is_active=True,
        )
        self.db.add(user_role)

        # Create session and tokens
        session, token_pair = await self._create_session_and_tokens(
            user=user,
            roles=[default_role.name],
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.db.commit()

        logger.info(f"New user registered: {user.email} (id={user.id})")

        return AuthResponse(
            user=self._user_to_response(user, [default_role.name]),
            session=token_pair,
            message="Account created successfully",
        )

    # ── Login ───────────────────────────────────────────────────────

    async def login(
        self,
        request: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthResponse:
        """Authenticate a user and create a new session."""

        # Find user
        result = await self.db.execute(
            select(User).where(User.email == request.email, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()

        if not user or not user.hashed_password:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(request.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is deactivated. Contact support.")

        # Auto-migrate password hash if needed (bcrypt → argon2)
        if needs_rehash(user.hashed_password):
            new_hash, algorithm = hash_password(request.password)
            user.hashed_password = new_hash
            user.password_hash_algorithm = algorithm
            logger.info(f"Password hash migrated for user {user.id}")

        # Update login stats
        user.login_count = (user.login_count or 0) + 1
        user.last_login_at = datetime.now(timezone.utc)

        # Get user roles
        roles = await self._get_user_roles(user.id)

        # Create session
        session, token_pair = await self._create_session_and_tokens(
            user=user,
            roles=roles,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.db.commit()

        logger.info(f"User logged in: {user.email}")

        return AuthResponse(
            user=self._user_to_response(user, roles),
            session=token_pair,
            message="Login successful",
        )

    # ── Token Refresh ───────────────────────────────────────────────

    async def refresh_tokens(
        self,
        refresh_token_str: str,
        ip_address: str | None = None,
    ) -> TokenPair:
        """
        Rotate a refresh token — issue new access + refresh token pair.
        Implements token family tracking for replay attack detection.
        """
        from app.core.jwt import decode_token

        # Decode the refresh token
        payload = decode_token(refresh_token_str, expected_type="refresh")
        user_id = payload["sub"]
        family_id = payload.get("family_id")

        # Find the token in DB
        token_hash = hash_token(refresh_token_str)
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise ValueError("Refresh token not found")

        # If token is already revoked → replay attack! Revoke entire family
        if db_token.is_revoked:
            logger.warning(
                f"Refresh token replay attack detected for user {user_id}, "
                f"family {family_id}. Revoking all tokens in family."
            )
            await self._revoke_token_family(family_id)
            raise ValueError("Token has been revoked — possible replay attack")

        # Check expiration
        if db_token.expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh token has expired")

        # Revoke the old token
        db_token.is_revoked = True
        db_token.revoked_at = datetime.now(timezone.utc)
        db_token.revoked_reason = "rotated"

        # Get user and roles
        user_result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")

        roles = await self._get_user_roles(user.id)

        # Create new tokens (same family)
        settings = get_settings()
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            roles=roles,
        )
        new_refresh, expires_at = create_refresh_token(
            user_id=str(user.id),
            session_id=str(db_token.session_id),
            family_id=str(family_id),
        )

        # Store new refresh token
        new_token_hash = hash_token(new_refresh)
        new_db_token = RefreshToken(
            user_id=user.id,
            session_id=db_token.session_id,
            token_hash=new_token_hash,
            family_id=uuid.UUID(str(family_id)),
            expires_at=expires_at,
        )
        self.db.add(new_db_token)
        await self.db.commit()

        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── Logout ──────────────────────────────────────────────────────

    async def logout(self, user_id: str, session_id: str | None = None):
        """Revoke the current session."""
        uid = uuid.UUID(user_id)

        if session_id:
            # Revoke specific session
            sid = uuid.UUID(session_id)
            await self.db.execute(
                update(UserSession)
                .where(UserSession.id == sid, UserSession.user_id == uid)
                .values(is_active=False)
            )
            # Revoke all refresh tokens for this session
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.session_id == sid, RefreshToken.is_revoked == False)
                .values(
                    is_revoked=True,
                    revoked_at=datetime.now(timezone.utc),
                    revoked_reason="logout",
                )
            )
        await self.db.commit()
        logger.info(f"User {user_id} logged out")

    async def logout_all(self, user_id: str):
        """Revoke all sessions for a user."""
        uid = uuid.UUID(user_id)

        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == uid)
            .values(is_active=False)
        )
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == uid, RefreshToken.is_revoked == False)
            .values(
                is_revoked=True,
                revoked_at=datetime.now(timezone.utc),
                revoked_reason="logout_all",
            )
        )
        await self.db.commit()
        logger.info(f"All sessions revoked for user {user_id}")

    # ── Session Management ──────────────────────────────────────────

    async def get_active_sessions(
        self, user_id: str, current_session_id: str | None = None
    ) -> list[SessionInfo]:
        """List all active sessions for a user."""
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(UserSession)
            .where(UserSession.user_id == uid, UserSession.is_active == True)
            .order_by(UserSession.created_at.desc())
        )
        sessions = result.scalars().all()

        return [
            SessionInfo(
                id=str(s.id),
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                device_info=s.device_info,
                last_activity_at=s.last_activity_at,
                created_at=s.created_at,
                is_current=(str(s.id) == current_session_id) if current_session_id else False,
            )
            for s in sessions
        ]

    # ── Private Helpers ─────────────────────────────────────────────

    async def _create_session_and_tokens(
        self,
        user: User,
        roles: list[str],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[UserSession, TokenPair]:
        """Create a new session and issue access + refresh tokens."""
        settings = get_settings()
        from datetime import timedelta

        # Create session record
        session = UserSession(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            is_active=True,
            last_activity_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(session)
        await self.db.flush()

        # Create tokens
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            roles=roles,
        )
        refresh_token_str, expires_at = create_refresh_token(
            user_id=str(user.id),
            session_id=str(session.id),
        )

        # Store refresh token hash
        token_record = RefreshToken(
            user_id=user.id,
            session_id=session.id,
            token_hash=hash_token(refresh_token_str),
            family_id=session.id,  # new family = session ID
            expires_at=expires_at,
        )
        self.db.add(token_record)

        token_pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return session, token_pair

    async def _get_or_create_default_role(self) -> Role:
        """Get the 'viewer' role, creating it if it doesn't exist."""
        result = await self.db.execute(
            select(Role).where(Role.name == "viewer")
        )
        role = result.scalar_one_or_none()

        if not role:
            # Seed all default roles
            default_roles = [
                ("super_admin", "Super Admin", 100),
                ("admin", "Admin", 80),
                ("manager", "Manager", 60),
                ("ml_engineer", "ML Engineer", 40),
                ("data_scientist", "Data Scientist", 30),
                ("viewer", "Viewer", 10),
            ]
            for name, display, level in default_roles:
                existing = await self.db.execute(
                    select(Role).where(Role.name == name)
                )
                if not existing.scalar_one_or_none():
                    self.db.add(Role(
                        name=name,
                        display_name=display,
                        hierarchy_level=level,
                        is_system=True,
                    ))
            await self.db.flush()

            result = await self.db.execute(
                select(Role).where(Role.name == "viewer")
            )
            role = result.scalar_one()

        return role

    async def _get_user_roles(self, user_id: uuid.UUID) -> list[str]:
        """Get all active role names for a user."""
        result = await self.db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, UserRole.is_active == True)
        )
        roles = [row[0] for row in result.all()]
        return roles if roles else ["viewer"]

    async def _revoke_token_family(self, family_id: str):
        """Revoke all tokens in a family (replay attack response)."""
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == uuid.UUID(family_id),
                RefreshToken.is_revoked == False,
            )
            .values(
                is_revoked=True,
                revoked_at=datetime.now(timezone.utc),
                revoked_reason="replay_attack_detected",
            )
        )
        await self.db.commit()

    @staticmethod
    def _user_to_response(user: User, roles: list[str]) -> UserResponse:
        """Convert a User ORM model to a UserResponse schema."""
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            company_name=user.company_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=roles,
            created_at=user.created_at,
        )
