"""
Rate Limiting Module
Protects API endpoints from abuse and DDoS attacks
"""

import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, Request
from functools import wraps
import asyncio
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    For production, replace with Redis-based solution for distributed systems.
    """
    
    def __init__(self):
        # Structure: {key: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request should be rate limited.
        
        Args:
            key: Unique identifier (user_id, IP, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_limited, remaining_requests, retry_after_seconds)
        """
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds
            
            # Clean old entries
            self._requests[key] = [
                (ts, count) for ts, count in self._requests[key]
                if ts > window_start
            ]
            
            # Count requests in window
            total_requests = sum(count for _, count in self._requests[key])
            
            if total_requests >= max_requests:
                # Find when the oldest request will expire
                if self._requests[key]:
                    oldest_ts = min(ts for ts, _ in self._requests[key])
                    retry_after = int(oldest_ts + window_seconds - now) + 1
                else:
                    retry_after = window_seconds
                return True, 0, retry_after
            
            # Add this request
            self._requests[key].append((now, 1))
            remaining = max_requests - total_requests - 1
            
            return False, remaining, 0
    
    async def record_request(self, key: str) -> None:
        """Record a request for the given key"""
        async with self._lock:
            self._requests[key].append((time.time(), 1))


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    return _rate_limiter


# Rate limit configurations per endpoint type
RATE_LIMITS = {
    # LLM endpoints - expensive, limit heavily
    "chat": {"max_requests": 30, "window_seconds": 60},  # 30 requests/minute
    "brain": {"max_requests": 20, "window_seconds": 60},  # 20 requests/minute
    "automl": {"max_requests": 10, "window_seconds": 60},  # 10 requests/minute (heavy computation)
    
    # File uploads - moderate limits
    "upload": {"max_requests": 20, "window_seconds": 60},  # 20 uploads/minute
    
    # Auth endpoints - strict to prevent brute force
    "login": {"max_requests": 5, "window_seconds": 60},  # 5 attempts/minute
    "signup": {"max_requests": 3, "window_seconds": 60},  # 3 signups/minute
    "magic_link": {"max_requests": 3, "window_seconds": 300},  # 3 magic links/5 minutes
    
    # General API - reasonable limits
    "default": {"max_requests": 100, "window_seconds": 60},  # 100 requests/minute
}


def get_client_ip(request: Request) -> str:
    """Extract client IP, handling proxies"""
    # Check X-Forwarded-For header (behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


async def check_rate_limit(
    request: Request,
    endpoint_type: str = "default",
    user_id: Optional[str] = None
) -> None:
    """
    Check rate limit for a request. Raises HTTPException if limited.
    
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
    
    # Add rate limit headers to response (done via middleware typically)
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = limits["max_requests"]
