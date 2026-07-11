"""
Database module initialization
"""

from database.storage import (
    LocalStorage,
    get_storage,
)

from database.models import (
    UserRole,
    AdminRole,
    MessageRole,
    MemoryLayer,
    ProcessingStatus,
    Theme,
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    AdminUser,
    Conversation,
    ConversationCreate,
    Message,
    MessageCreate,
    UserFile,
    UserFileCreate,
    UserQuery,
    UserQueryCreate,
    UserMemory,
    UserMemoryCreate,
    UserPreferences,
    UserPreferencesUpdate,
    AuthSignUp,
    AuthLogin,
    AuthMagicLink,
    AuthResponse,
    AuthUser
)

from database.auth import (
    get_current_user,
    get_current_user_optional,
    get_admin_user,
    get_super_admin_user,
    get_auth_service,
    AuthService,
    decode_jwt
)

__all__ = [
    # Storage
    "get_storage",
    "LocalStorage",
    
    # Enums
    "UserRole",
    "AdminRole",
    "MessageRole",
    "MemoryLayer",
    "ProcessingStatus",
    "Theme",
    
    # Models
    "UserProfile",
    "UserProfileCreate",
    "UserProfileUpdate",
    "AdminUser",
    "Conversation",
    "ConversationCreate",
    "Message",
    "MessageCreate",
    "UserFile",
    "UserFileCreate",
    "UserQuery",
    "UserQueryCreate",
    "UserMemory",
    "UserMemoryCreate",
    "UserPreferences",
    "UserPreferencesUpdate",
    "AuthSignUp",
    "AuthLogin",
    "AuthMagicLink",
    "AuthResponse",
    "AuthUser",
    
    # Auth
    "get_current_user",
    "get_current_user_optional",
    "get_admin_user",
    "get_super_admin_user",
    "get_auth_service",
    "AuthService",
    "decode_jwt"
]
