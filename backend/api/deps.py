from fastapi import Header, HTTPException, Depends
from typing import Optional

async def get_current_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")):
    """
    Simulates a secure user extraction. 
    In a real production app with Supabase/Auth0, this would verify a JWT.
    Here we enforce that the ID comes from the Header (likely set by API Gateway/Frontend Auth)
    and NOT the request body.
    """
    if not x_user_id:
        # For development/fallback if header missing, you might check a cookie or query param
        # But for strict security, we fail.
        raise HTTPException(status_code=401, detail="Missing Authentication Header (X-User-ID)")
    
    return x_user_id
