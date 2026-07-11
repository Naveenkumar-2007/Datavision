"""
Rate Limiting Module — Redis + In-Memory
==========================================
Protects API endpoints from abuse and DDoS attacks.

Backend Selection:
  - If REDIS_URL is set → uses Redis INCR + TTL (survives restarts, works multi-worker)
  - Otherwise → uses in-memory sliding window (single-process only)

Usage:
  from core.rate_limiter import check_rate_limit
  await check_rate_limit(request, "chat", user_id)
"""

import os
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

logger = logging.getLogger(__name__)


# =============================================================================
# RATE LIMIT CONFIGURATIONS
# =============================================================================

RATE_LIMITS = {
    # LLM endpoints — expensive, limit heavily
    "chat": {"max_requests": 30, "window_seconds": 60},
    "brain": {"max_requests": 20, "window_seconds": 60},
    "automl": {"max_requests": 10, "window_seconds": 60},

    # File uploads — moderate limits
    "upload": {"max_requests": 20, "window_seconds": 60},

    # Auth endpoints — strict to prevent brute force
    "login": {"max_requests": 5, "window_seconds": 60},
    "signup": {"max_requests": 3, "window_seconds": 60},
    "magic_link": {"max_requests": 3, "window_seconds": 300},

    # Deploy — moderate (each deploy is heavy)
    "deploy": {"max_requests": 5, "window_seconds": 60},

    # Reports — moderate (can be CPU-intensive)
    "report": {"max_requests": 10, "window_seconds": 60},
    "report_generate": {"max_requests": 5, "window_seconds": 60},  # LLM-backed generation

    # Developer API — moderate
    "developer": {"max_requests": 20, "window_seconds": 60},

    # Collaboration — reasonable for chat-like usage
    "collaboration": {"max_requests": 60, "window_seconds": 60},
    "collab_message": {"max_requests": 30, "window_seconds": 60},  # posting messages

    # General API — reasonable limits
    "default": {"max_requests": 100, "window_seconds": 60},
}


# =============================================================================
# IN-MEMORY RATE LIMITER (fallback)
# =============================================================================

class InMemoryRateLimiter:
    """
    In-memory sliding window rate limiter.
    Works for single-process deployments. State is lost on restart.
    """

    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
        logger.info("⚡ Rate limiter: in-memory backend (single-process)")

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request should be rate limited.

        Returns:
            Tuple of (is_limited, remaining_requests, retry_after_seconds)
        """
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds

            # Clean old entries
            self._requests[key] = [
                ts for ts in self._requests[key]
                if ts > window_start
            ]

            total_requests = len(self._requests[key])

            if total_requests >= max_requests:
                if self._requests[key]:
                    oldest_ts = min(self._requests[key])
                    retry_after = int(oldest_ts + window_seconds - now) + 1
                else:
                    retry_after = window_seconds
                return True, 0, max(1, retry_after)

            # Record this request
            self._requests[key].append(now)
            remaining = max_requests - total_requests - 1

            return False, remaining, 0

    async def get_usage(self, key: str, window_seconds: int = 60) -> int:
        """Get the number of requests in the current window."""
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds
            self._requests[key] = [
                ts for ts in self._requests[key]
                if ts > window_start
            ]
            return len(self._requests[key])


# =============================================================================
# REDIS RATE LIMITER
# =============================================================================

class RedisRateLimiter:
    """
    Redis-backed rate limiter using INCR + EXPIRE.
    Survives server restarts, works across multiple workers.
    """

    def __init__(self, redis_url: str):
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        self._prefix = "dv:rl:"
        logger.info(f"⚡ Rate limiter: Redis backend ({redis_url.split('@')[-1] if '@' in redis_url else redis_url})")

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Fixed-window counter using Redis INCR + EXPIRE.

        Returns:
            Tuple of (is_limited, remaining_requests, retry_after_seconds)
        """
        redis_key = f"{self._prefix}{key}"

        try:
            pipe = self._redis.pipeline()
            pipe.incr(redis_key)
            pipe.ttl(redis_key)
            results = await pipe.execute()

            current_count = results[0]
            ttl = results[1]

            # Set expiry on first request in window
            if ttl == -1:
                await self._redis.expire(redis_key, window_seconds)
                ttl = window_seconds

            if current_count > max_requests:
                retry_after = max(1, ttl)
                return True, 0, retry_after

            remaining = max_requests - current_count
            return False, remaining, 0

        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}, allowing request")
            return False, max_requests, 0

    async def get_usage(self, key: str, window_seconds: int = 60) -> int:
        """Get the current count for a key."""
        redis_key = f"{self._prefix}{key}"
        try:
            count = await self._redis.get(redis_key)
            return int(count) if count else 0
        except Exception:
            return 0


# =============================================================================
# FACTORY & SINGLETON
# =============================================================================

_rate_limiter = None


def get_rate_limiter():
    """Get the global rate limiter instance (auto-selects Redis or in-memory)."""
    global _rate_limiter
    if _rate_limiter is None:
        redis_url = os.getenv("REDIS_URL", "").strip()
        if redis_url:
            try:
                _rate_limiter = RedisRateLimiter(redis_url)
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}), falling back to in-memory")
                _rate_limiter = InMemoryRateLimiter()
        else:
            _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


# =============================================================================
# HELPERS
# =============================================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP, handling proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


async def check_rate_limit(
    request: Request,
    endpoint_type: str = "default",
    user_id: Optional[str] = None
) -> None:
    """
    Check rate limit for a request. Raises HTTPException(429) if limited.

    Args:
        request: FastAPI Request object
        endpoint_type: Type of endpoint for specific limits
        user_id: User ID if authenticated (for per-user limits)
    """
    limiter = get_rate_limiter()
    limits = RATE_LIMITS.get(endpoint_type, RATE_LIMITS["default"])

    # Use user_id if available, otherwise use IP
    if user_id:
        key = f"user:{user_id}:{endpoint_type}"
    else:
        ip = get_client_ip(request)
        key = f"ip:{ip}:{endpoint_type}"

    is_limited, remaining, retry_after = await limiter.is_rate_limited(
        key,
        limits["max_requests"],
        limits["window_seconds"]
    )

    if is_limited:
        logger.warning(f"Rate limit exceeded for {key}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too many requests",
                "message": f"Rate limit exceeded. Please try again in {retry_after} seconds.",
                "retry_after": retry_after
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limits["max_requests"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + retry_after)
            }
        )

    # Stash headers for the middleware to pick up
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = limits["max_requests"]


# =============================================================================
# FASTAPI MIDDLEWARE
# =============================================================================

class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches X-RateLimit-* headers to every response.
    Headers are set by check_rate_limit() on request.state.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Attach rate limit headers if they were set by check_rate_limit()
        remaining = getattr(request.state, "rate_limit_remaining", None)
        limit = getattr(request.state, "rate_limit_limit", None)

        if remaining is not None and limit is not None:
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response
