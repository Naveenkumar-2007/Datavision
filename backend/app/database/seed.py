"""
Database Seed Script — Populates initial roles, permissions, and the super admin user.

Run after migrations:
    python -m app.database.seed

Or from the project root:
    python backend/app/database/seed.py
"""

import asyncio
import os
import sys
import uuid
import logging

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session_factory, dispose_engine
from app.models.rbac import Role, Permission, RolePermission
from app.models.user import User, UserPreferences
from app.models.rbac import UserRole
from app.core.security import hash_password

logger = logging.getLogger(__name__)

# ── Role Definitions ────────────────────────────────────────────────

ROLES = [
    {
        "name": "super_admin",
        "display_name": "Super Admin",
        "description": "Full system access. Can manage all users, roles, and settings.",
        "hierarchy_level": 100,
        "is_system": True,
    },
    {
        "name": "admin",
        "display_name": "Admin",
        "description": "Administrative access. Can manage users and platform settings.",
        "hierarchy_level": 80,
        "is_system": True,
    },
    {
        "name": "manager",
        "display_name": "Manager",
        "description": "Team management. Can manage projects, models, and datasets.",
        "hierarchy_level": 60,
        "is_system": True,
    },
    {
        "name": "ml_engineer",
        "display_name": "ML Engineer",
        "description": "Build, train, and deploy ML models.",
        "hierarchy_level": 40,
        "is_system": True,
    },
    {
        "name": "data_scientist",
        "display_name": "Data Scientist",
        "description": "Explore data, create experiments, and build models.",
        "hierarchy_level": 30,
        "is_system": True,
    },
    {
        "name": "viewer",
        "display_name": "Viewer",
        "description": "Read-only access to projects, models, and datasets.",
        "hierarchy_level": 10,
        "is_system": True,
    },
]

# ── Permission Definitions ──────────────────────────────────────────

PERMISSIONS = [
    # Users
    ("users:read", "View Users", "View user profiles", "users", "read"),
    ("users:write", "Edit Users", "Edit user profiles", "users", "write"),
    ("users:delete", "Delete Users", "Soft-delete user accounts", "users", "delete"),
    # Projects
    ("projects:read", "View Projects", "View project details", "projects", "read"),
    ("projects:write", "Edit Projects", "Create and edit projects", "projects", "write"),
    ("projects:delete", "Delete Projects", "Delete projects", "projects", "delete"),
    # Models
    ("models:read", "View Models", "View ML models", "models", "read"),
    ("models:write", "Edit Models", "Create and edit ML models", "models", "write"),
    ("models:deploy", "Deploy Models", "Deploy ML models to production", "models", "deploy"),
    # Datasets
    ("datasets:read", "View Datasets", "View datasets", "datasets", "read"),
    ("datasets:write", "Edit Datasets", "Upload and edit datasets", "datasets", "write"),
    ("datasets:delete", "Delete Datasets", "Delete datasets", "datasets", "delete"),
    # Experiments
    ("experiments:read", "View Experiments", "View experiments", "experiments", "read"),
    ("experiments:write", "Edit Experiments", "Create and run experiments", "experiments", "write"),
    # Admin
    ("admin:dashboard", "Admin Dashboard", "Access admin dashboard", "admin", "dashboard"),
    ("admin:audit_logs", "Audit Logs", "View audit logs", "admin", "audit_logs"),
    # System
    ("system:settings", "System Settings", "Manage system settings", "system", "settings"),
]

# ── Role → Permission Mapping ──────────────────────────────────────

ROLE_PERMISSIONS = {
    "super_admin": ["*"],  # Gets all permissions
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


async def seed_roles(db: AsyncSession) -> dict[str, uuid.UUID]:
    """Seed system roles. Returns {role_name: role_id}."""
    role_map = {}

    for role_data in ROLES:
        result = await db.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            role_map[existing.name] = existing.id
            print(f"  Role '{existing.name}' already exists")
        else:
            role = Role(**role_data)
            db.add(role)
            await db.flush()
            role_map[role.name] = role.id
            print(f"  Created role '{role.name}' (level={role.hierarchy_level})")

    return role_map


async def seed_permissions(db: AsyncSession) -> dict[str, uuid.UUID]:
    """Seed permissions. Returns {codename: permission_id}."""
    perm_map = {}

    for codename, display_name, description, resource, action in PERMISSIONS:
        result = await db.execute(
            select(Permission).where(Permission.codename == codename)
        )
        existing = result.scalar_one_or_none()

        if existing:
            perm_map[existing.codename] = existing.id
        else:
            perm = Permission(
                codename=codename,
                display_name=display_name,
                description=description,
                resource=resource,
                action=action,
            )
            db.add(perm)
            await db.flush()
            perm_map[perm.codename] = perm.id
            print(f"  Created permission '{codename}'")

    return perm_map


async def seed_role_permissions(
    db: AsyncSession,
    role_map: dict[str, uuid.UUID],
    perm_map: dict[str, uuid.UUID],
):
    """Assign permissions to roles."""
    all_perm_codenames = list(perm_map.keys())

    for role_name, permission_codenames in ROLE_PERMISSIONS.items():
        role_id = role_map.get(role_name)
        if not role_id:
            continue

        # super_admin gets everything
        codenames = all_perm_codenames if "*" in permission_codenames else permission_codenames

        for codename in codenames:
            perm_id = perm_map.get(codename)
            if not perm_id:
                continue

            # Check if already assigned
            result = await db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == perm_id,
                )
            )
            if result.scalar_one_or_none():
                continue

            db.add(RolePermission(role_id=role_id, permission_id=perm_id))

    await db.flush()
    print("  Role-permission assignments complete")


async def seed_super_admin(db: AsyncSession, role_map: dict[str, uuid.UUID]):
    """Create the initial super admin user if none exists."""

    # Check if any super admin exists
    result = await db.execute(
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(Role.name == "super_admin")
    )
    if result.scalar_one_or_none():
        print("  Super admin already exists, skipping")
        return

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@datavision.ai")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@DataVision2024!")

    hashed, algorithm = hash_password(admin_password)

    user = User(
        email=admin_email,
        hashed_password=hashed,
        password_hash_algorithm=algorithm,
        full_name="System Administrator",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    # Assign super_admin role
    super_admin_role_id = role_map.get("super_admin")
    if super_admin_role_id:
        db.add(UserRole(user_id=user.id, role_id=super_admin_role_id, is_active=True))

    # Create default preferences
    db.add(UserPreferences(user_id=user.id))

    await db.flush()
    print(f"  Created super admin: {admin_email}")
    print(f"  DEFAULT PASSWORD: {admin_password}")
    print(f"  >>> CHANGE THIS IN PRODUCTION! <<<")


async def run_seed():
    """Run all seed operations."""
    print("\n=== DataVision Database Seed ===\n")

    factory = get_session_factory()
    async with factory() as db:
        try:
            print("[1/4] Seeding roles...")
            role_map = await seed_roles(db)

            print("[2/4] Seeding permissions...")
            perm_map = await seed_permissions(db)

            print("[3/4] Assigning permissions to roles...")
            await seed_role_permissions(db, role_map, perm_map)

            print("[4/4] Creating super admin user...")
            await seed_super_admin(db, role_map)

            await db.commit()
            print("\n=== Seed complete ===\n")

        except Exception as e:
            await db.rollback()
            print(f"\nSeed failed: {e}")
            raise
        finally:
            await dispose_engine()


if __name__ == "__main__":
    # Import Permission model (needed for forward reference)
    from app.models.rbac import Permission  # noqa: F811
    asyncio.run(run_seed())
