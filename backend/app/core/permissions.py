"""
RBAC Permissions — FastAPI dependency injection for role and permission checks.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.jwt import decode_token


# Role hierarchy — higher level = more permissions
ROLE_HIERARCHY: dict[str, int] = {
    "super_admin": 100,
    "admin": 80,
    "manager": 60,
    "ml_engineer": 40,
    "data_scientist": 30,
    "viewer": 10,
}

# Default permissions per role
DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "super_admin": ["*"],  # All permissions
    "admin": [
        "users:read", "users:write", "users:delete",
        "projects:read", "projects:write", "projects:delete",
        "models:read", "models:write", "models:deploy",
        "datasets:read", "datasets:write", "datasets:delete",
        "experiments:read", "experiments:write",
        "admin:dashboard", "admin:audit_logs",
        "system:settings",
    ],
    "manager": [
        "users:read",
        "projects:read", "projects:write",
        "models:read", "models:write", "models:deploy",
        "datasets:read", "datasets:write",
        "experiments:read", "experiments:write",
    ],
    "ml_engineer": [
        "projects:read",
        "models:read", "models:write", "models:deploy",
        "datasets:read", "datasets:write",
        "experiments:read", "experiments:write",
    ],
    "data_scientist": [
        "projects:read",
        "models:read", "models:write",
        "datasets:read", "datasets:write",
        "experiments:read", "experiments:write",
    ],
    "viewer": [
        "projects:read",
        "models:read",
        "datasets:read",
        "experiments:read",
    ],
}


_security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Represents the currently authenticated user from a JWT token."""

    def __init__(self, payload: dict):
        self.id: str = payload["sub"]
        self.email: str = payload.get("email", "")
        self.roles: list[str] = payload.get("roles", [])
        self.token_type: str = payload.get("type", "access")

    @property
    def highest_role(self) -> str:
        """Get the user's highest privilege role."""
        if not self.roles:
            return "viewer"
        return max(self.roles, key=lambda r: ROLE_HIERARCHY.get(r, 0))

    @property
    def hierarchy_level(self) -> int:
        """Get the user's highest hierarchy level."""
        return ROLE_HIERARCHY.get(self.highest_role, 0)

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role or higher."""
        required_level = ROLE_HIERARCHY.get(role_name, 0)
        return self.hierarchy_level >= required_level

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission via their roles."""
        for role in self.roles:
            perms = DEFAULT_ROLE_PERMISSIONS.get(role, [])
            if "*" in perms or permission in perms:
                return True
        return False

    def __repr__(self) -> str:
        return f"<AuthenticatedUser id={self.id} roles={self.roles}>"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> AuthenticatedUser:
    """
    FastAPI dependency — extracts and validates the current user from JWT.
    Raises 401 if no valid token is present.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials, expected_type="access")
    return AuthenticatedUser(payload)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> AuthenticatedUser | None:
    """
    FastAPI dependency — returns the current user or None for anonymous access.
    """
    if not credentials:
        return None

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
        return AuthenticatedUser(payload)
    except HTTPException:
        return None


def require_role(minimum_role: str):
    """
    FastAPI dependency factory — ensures user has at least the given role.

    Usage:
        @router.get("/admin/users")
        async def list_users(user: AuthenticatedUser = Depends(require_role("admin"))):
            ...
    """
    async def _check_role(
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not user.has_role(minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {minimum_role} or higher",
            )
        return user

    return _check_role


def require_permission(permission: str):
    """
    FastAPI dependency factory — ensures user has a specific permission.

    Usage:
        @router.post("/models/deploy")
        async def deploy(user: AuthenticatedUser = Depends(require_permission("models:deploy"))):
            ...
    """
    async def _check_permission(
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user

    return _check_permission
