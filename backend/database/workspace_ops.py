"""
Workspace Operations Module - PostgreSQL replacements for Supabase admin functions.

Replaces: utils/supabase_admin.py
Provides: get_workspace_members, get_user_email, is_workspace_member
"""
import uuid
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from database.orm import WorkspaceMember, UserProfile


async def get_workspace_members(db: AsyncSession, workspace_id: str) -> List[Dict]:
    """
    Get all members of a workspace with their roles.
    Replaces: supabase_admin.get_workspace_members()
    """
    try:
        ws_id = uuid.UUID(workspace_id)
    except (ValueError, AttributeError):
        return []

    stmt = (
        select(WorkspaceMember.user_id, WorkspaceMember.role)
        .where(WorkspaceMember.workspace_id == ws_id)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [{"user_id": str(row.user_id), "role": row.role} for row in rows]


async def get_user_email(db: AsyncSession, user_id: str) -> Optional[str]:
    """
    Get a user's email address by their ID.
    Replaces: supabase_admin.get_user_email()
    """
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        return None

    stmt = select(UserProfile.email).where(UserProfile.id == uid)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    return row


async def is_workspace_member(db: AsyncSession, workspace_id: str, user_id: str) -> bool:
    """
    Check if a user is a member of a workspace.
    Replaces: supabase_admin.is_workspace_member()
    """
    try:
        ws_id = uuid.UUID(workspace_id)
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        return False

    stmt = (
        select(func.count())
        .select_from(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == ws_id,
            WorkspaceMember.user_id == uid
        )
    )
    result = await db.execute(stmt)
    count = result.scalar()
    return count > 0


async def add_workspace_member(
    db: AsyncSession,
    workspace_id: str,
    user_id: str,
    role: str = "member"
) -> Optional[WorkspaceMember]:
    """Add a user to a workspace."""
    try:
        member = WorkspaceMember(
            workspace_id=uuid.UUID(workspace_id),
            user_id=uuid.UUID(user_id),
            role=role
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member
    except Exception:
        await db.rollback()
        return None
