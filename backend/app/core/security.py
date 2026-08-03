"""
Security Module — Password hashing and validation.

Supports Argon2id (recommended) with automatic bcrypt migration on login.
"""

import re
import hashlib
import secrets
from typing import Optional

from passlib.context import CryptContext


# Argon2id is the primary hasher; bcrypt is kept for backward compatibility
_pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    deprecated=["bcrypt"],
    argon2__rounds=4,
    argon2__memory_cost=65536,
    argon2__parallelism=2,
)


def hash_password(password: str) -> tuple[str, str]:
    """
    Hash a password using Argon2id.
    Returns (hashed_password, algorithm_name).
    """
    return _pwd_context.hash(password), "argon2"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Works with both Argon2 and legacy bcrypt hashes.
    """
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be upgraded (e.g., bcrypt → argon2).
    Call this after successful login to auto-migrate hashes.
    """
    return _pwd_context.needs_update(hashed_password)


def validate_password_strength(password: str) -> Optional[str]:
    """
    Validate password meets minimum security requirements.
    Returns error message if invalid, None if valid.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if len(password) > 128:
        return "Password must be at most 128 characters long"
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r"\d", password):
        return "Password must contain at least one digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/~`]", password):
        return "Password must contain at least one special character"
    return None


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash a token for storage (SHA-256). Used for refresh tokens, API keys."""
    return hashlib.sha256(token.encode()).hexdigest()
