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

# Create admin client only if credentials are available
supabase_admin: Optional[Client] = None

if SERVICE_ROLE_KEY and SUPABASE_URL:
    try:
        supabase_admin = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
        print("✅ Supabase admin client initialized")
    except Exception as e:
        print(f"⚠️ Failed to initialize Supabase admin client: {e}")
else:
    print("⚠️ Supabase credentials not configured - some features will be disabled")


def get_supabase_admin() -> Optional[Client]:
    """Get Supabase admin client with service role privileges"""
    return supabase_admin


# Helper functions for common operations
async def get_workspace_members(workspace_id: str) -> list:
    """Get all members of a workspace"""
    if not supabase_admin:
        return []
    response = supabase_admin.table("workspace_members").select("user_id, role").eq("workspace_id", workspace_id).execute()
    return response.data or []


async def get_user_email(user_id: str) -> Optional[str]:
    """Get user email from auth.users"""
    if not supabase_admin:
        return None
    try:
        response = supabase_admin.auth.admin.get_user_by_id(user_id)
        return response.user.email if response.user else None
    except Exception as e:
        print(f"Error getting user email: {e}")
        return None


async def verify_workspace_membership(user_id: str, workspace_id: str) -> bool:
    """Verify user is member of workspace"""
    if not supabase_admin:
        return False
    response = supabase_admin.table("workspace_members").select("user_id").eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
    return len(response.data) > 0 if response.data else False
