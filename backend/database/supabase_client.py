"""
Supabase Client Module
Singleton client for database and storage operations
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration - MUST be set via environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Validate required configuration
if not SUPABASE_URL:
    print("⚠️ CRITICAL: SUPABASE_URL not configured. Set in environment variables.")

# Singleton clients
_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Get Supabase client with anon key (for user-context operations).
    Use this when you have a user's JWT token.
    """
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_ANON_KEY:
            print("⚠️ SUPABASE_ANON_KEY not configured")
            return None
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase_client


def get_supabase_admin_client() -> Optional[Client]:
    """
    Get Supabase client with service role key (for admin operations).
    Use this for operations that bypass RLS.
    WARNING: Only use for server-side admin operations!
    """
    global _supabase_admin_client
    if _supabase_admin_client is None:
        if not SUPABASE_SERVICE_ROLE_KEY:
            print("⚠️ SUPABASE_SERVICE_ROLE_KEY not configured")
            return None
        _supabase_admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin_client


def get_user_client(access_token: str) -> Optional[Client]:
    """
    Get Supabase client authenticated with user's access token.
    This respects RLS policies.
    """
    if not SUPABASE_ANON_KEY:
        print("⚠️ SUPABASE_ANON_KEY not configured")
        return None
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.auth.set_session(access_token, "")
    return client


# Storage bucket name
STORAGE_BUCKET = "user-files"


class SupabaseStorage:
    """Helper class for Supabase Storage operations"""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_admin_client()
        self.bucket = STORAGE_BUCKET
        self.available = self.client is not None
    
    def upload_file(self, user_id: str, filename: str, file_data: bytes, content_type: str = "application/octet-stream") -> dict:
        """
        Upload a file to user's folder in storage.
        Path format: {user_id}/{filename}
        """
        path = f"{user_id}/{filename}"
        
        try:
            response = self.client.storage.from_(self.bucket).upload(
                path=path,
                file=file_data,
                file_options={"content-type": content_type}
            )
            return {"success": True, "path": path, "response": response}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_file(self, user_id: str, filename: str) -> bytes:
        """Download a file from user's folder"""
        path = f"{user_id}/{filename}"
        response = self.client.storage.from_(self.bucket).download(path)
        return response
    
    def delete_file(self, user_id: str, filename: str) -> dict:
        """Delete a file from user's folder"""
        path = f"{user_id}/{filename}"
        try:
            response = self.client.storage.from_(self.bucket).remove([path])
            return {"success": True, "response": response}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_files(self, user_id: str) -> list:
        """List all files in user's folder"""
        try:
            response = self.client.storage.from_(self.bucket).list(user_id)
            return response
        except Exception as e:
            return []
    
    def get_public_url(self, user_id: str, filename: str) -> str:
        """Get public URL for a file (if bucket is public)"""
        path = f"{user_id}/{filename}"
        return self.client.storage.from_(self.bucket).get_public_url(path)
    
    def get_signed_url(self, user_id: str, filename: str, expires_in: int = 3600) -> str:
        """Get signed URL for private file access"""
        path = f"{user_id}/{filename}"
        response = self.client.storage.from_(self.bucket).create_signed_url(path, expires_in)
        return response.get("signedURL", "")


# Convenience function
def get_storage() -> SupabaseStorage:
    """Get storage helper instance"""
    return SupabaseStorage()
