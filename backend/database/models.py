"""
Database Models
Pydantic models for Supabase tables
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AdminRole(str, Enum):
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MemoryLayer(str, Enum):
    MID_TERM = "mid_term"
    LONG_TERM = "long_term"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


# ============================================================================
# USER MODELS
# ============================================================================

class UserProfile(BaseModel):
    """User profile model"""
    id: str  # UUID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    company_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserProfileCreate(BaseModel):
    """Create user profile"""
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """Update user profile"""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    company_name: Optional[str] = None


class AdminUser(BaseModel):
    """Admin user model"""
    id: str
    user_id: str
    admin_role: AdminRole = AdminRole.MODERATOR
    permissions: dict = {}
    granted_by: Optional[str] = None
    granted_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    notes: Optional[str] = None


# ============================================================================
# CONVERSATION MODELS
# ============================================================================

class Conversation(BaseModel):
    """Conversation model"""
    id: str
    user_id: str
    title: Optional[str] = None
    mode: str = "auto"
    is_archived: bool = False
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ConversationCreate(BaseModel):
    """Create conversation"""
    title: Optional[str] = None
    mode: str = "auto"


class Message(BaseModel):
    """Message model"""
    id: str
    conversation_id: str
    user_id: str
    role: MessageRole
    content: str
    mode: Optional[str] = None
    sources: Optional[List[str]] = None
    metadata: dict = {}
    created_at: datetime = Field(default_factory=datetime.now)


class MessageCreate(BaseModel):
    """Create message"""
    conversation_id: str
    role: MessageRole
    content: str
    mode: Optional[str] = None
    sources: Optional[List[str]] = None
    metadata: dict = {}


# ============================================================================
# FILE MODELS
# ============================================================================

class UserFile(BaseModel):
    """User file metadata model"""
    id: str
    user_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    storage_path: str
    bucket_name: str = "user-files"
    is_processed: bool = False
    is_indexed: bool = False
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_error: Optional[str] = None
    metadata: dict = {}
    uploaded_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None


class UserFileCreate(BaseModel):
    """Create user file record"""
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    storage_path: str
    metadata: dict = {}


# ============================================================================
# QUERY MODELS
# ============================================================================

class UserQuery(BaseModel):
    """User query log model"""
    id: str
    user_id: str
    conversation_id: Optional[str] = None
    query_text: str
    query_type: Optional[str] = None
    response_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cache_hit: bool = False
    sources_used: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.now)


class UserQueryCreate(BaseModel):
    """Create query log"""
    conversation_id: Optional[str] = None
    query_text: str
    query_type: Optional[str] = None
    response_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cache_hit: bool = False
    sources_used: Optional[List[str]] = None


# ============================================================================
# MEMORY MODELS
# ============================================================================

class UserMemory(BaseModel):
    """User memory model"""
    id: str
    user_id: str
    memory_layer: MemoryLayer
    memory_type: str
    content: dict
    embedding: Optional[List[float]] = None
    metadata: dict = {}
    confidence: Optional[float] = None
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserMemoryCreate(BaseModel):
    """Create memory entry"""
    memory_layer: MemoryLayer
    memory_type: str
    content: dict
    metadata: dict = {}
    confidence: Optional[float] = None
    expires_at: Optional[datetime] = None


# ============================================================================
# PREFERENCES MODELS
# ============================================================================

class UserPreferences(BaseModel):
    """User preferences model"""
    id: str
    user_id: str
    theme: Theme = Theme.DARK
    currency_code: str = "INR"
    currency_symbol: str = "₹"
    language: str = "en"
    notifications_enabled: bool = True
    email_notifications: bool = True
    auto_save_conversations: bool = True
    default_chat_mode: str = "auto"
    custom_settings: dict = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserPreferencesUpdate(BaseModel):
    """Update user preferences"""
    theme: Optional[Theme] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    language: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    auto_save_conversations: Optional[bool] = None
    default_chat_mode: Optional[str] = None
    custom_settings: Optional[dict] = None


# ============================================================================
# AUTH MODELS
# ============================================================================

class AuthSignUp(BaseModel):
    """Signup request"""
    email: str
    password: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class AuthLogin(BaseModel):
    """Login request"""
    email: str
    password: str


class AuthMagicLink(BaseModel):
    """Magic link request"""
    email: str


class AuthResponse(BaseModel):
    """Auth response"""
    user: Optional[UserProfile] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None
    message: Optional[str] = None


class AuthUser(BaseModel):
    """Authenticated user from JWT"""
    id: str
    email: str
    role: UserRole = UserRole.USER
    is_admin: bool = False
