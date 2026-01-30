"""
Input Validation Module
Centralized input validation for all API endpoints
"""

import re
from typing import Optional, List, Any
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


# Common regex patterns
PATTERNS = {
    "email": re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    "uuid": re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I),
    "user_id": re.compile(r'^[a-zA-Z0-9_-]{1,128}$'),
    "filename": re.compile(r'^[a-zA-Z0-9_.-]{1,255}$'),
    "alphanumeric": re.compile(r'^[a-zA-Z0-9_-]+$'),
}


def validate_email(email: str) -> str:
    """Validate email format"""
    if not email or not PATTERNS["email"].match(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return email.lower().strip()


def validate_user_id(user_id: str) -> str:
    """Validate user ID format"""
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Check for path traversal
    if '..' in user_id or '/' in user_id or '\\' in user_id:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if not PATTERNS["user_id"].match(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    return user_id


def validate_filename(filename: str) -> str:
    """Validate filename format"""
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Remove path components
    import os
    filename = os.path.basename(filename)
    
    # Check for path traversal
    if '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    if len(filename) > 255:
        raise HTTPException(status_code=400, detail="Filename too long")
    
    return filename


def validate_query(query: str, max_length: int = 5000) -> str:
    """Validate chat query"""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    query = query.strip()
    
    if len(query) > max_length:
        raise HTTPException(status_code=400, detail=f"Query too long (max {max_length} characters)")
    
    return query


def validate_pagination(page: int = 1, limit: int = 20) -> tuple:
    """Validate pagination parameters"""
    if page < 1:
        page = 1
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100
    return page, limit


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize a string input"""
    if not value:
        return ""
    
    # Remove null bytes and control characters
    value = "".join(char for char in value if ord(char) >= 32 or char in "\n\t")
    
    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


def validate_json_payload(data: Any, required_fields: List[str] = None) -> dict:
    """Validate JSON payload"""
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing)}"
            )
    
    return data


# Pydantic models with validation
class ChatRequest(BaseModel):
    """Validated chat request model"""
    query: str = Field(..., min_length=1, max_length=10000)
    user_id: str = Field(..., min_length=1, max_length=128, pattern=r'^[a-zA-Z0-9_-]+$')
    mode: Optional[str] = Field(default="auto", max_length=50)
    conversation_id: Optional[str] = Field(default=None, max_length=128)
    
    @validator('query')
    def validate_query(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be empty')
        return v
    
    @validator('user_id')
    def validate_user_id_field(cls, v):
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid user ID')
        return v


class FileUploadRequest(BaseModel):
    """Validated file upload metadata"""
    user_id: str = Field(..., min_length=1, max_length=128, pattern=r'^[a-zA-Z0-9_-]+$')
    
    @validator('user_id')
    def validate_user_id_field(cls, v):
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid user ID')
        return v


class AuthRequest(BaseModel):
    """Validated auth request model"""
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('email')
    def validate_email(cls, v):
        v = v.lower().strip()
        if not PATTERNS["email"].match(v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        # Check for basic complexity
        if not re.search(r'[A-Za-z]', v) or not re.search(r'[0-9]', v):
            raise ValueError('Password must contain letters and numbers')
        return v
