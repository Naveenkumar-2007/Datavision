"""
Supabase Admin Client - Server-side only
Uses SERVICE_ROLE_KEY for privileged operations
"""

import os
from supabase import create_client, Client
from typing import Optional

# CRITICAL: This key has full access - NEVER expose to client
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SERVICE_ROLE_KEY or not SUPABASE_URL:
    raise ValueError("Missing SUPABASE_SERVICE_ROLE_KEY or SUPABASE_URL environment variables")

# Create admin client with service role key
supabase_admin: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)


def get_supabase_admin() -> Client:
    """Get Supabase admin client with service role privileges"""
    return supabase_admin


# Helper functions for common operations
async def get_workspace_members(workspace_id: str) -> list:
    """Get all members of a workspace"""
    response = supabase_admin.table("workspace_members").select("user_id, role").eq("workspace_id", workspace_id).execute()
    return response.data or []


async def get_user_email(user_id: str) -> Optional[str]:
    """Get user email from auth.users"""
    try:
        response = supabase_admin.auth.admin.get_user_by_id(user_id)
        return response.user.email if response.user else None
    except Exception as e:
        print(f"Error getting user email: {e}")
        return None


async def verify_workspace_membership(user_id: str, workspace_id: str) -> bool:
    """Verify user is member of workspace"""
    response = supabase_admin.table("workspace_members").select("user_id").eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
    return len(response.data) > 0 if response.data else False
