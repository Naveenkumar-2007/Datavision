"""
Structured Logging — JSON-formatted logs with request correlation and sensitive data filtering.
"""

import logging
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# Patterns to redact from log output
_SENSITIVE_PATTERNS = [
    re.compile(r"(password|secret|token|api_key|authorization)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"(sk-[a-zA-Z0-9]+)", re.IGNORECASE),
    re.compile(r"(gsk_[a-zA-Z0-9]+)", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9._-]+", re.IGNORECASE),
]


def _redact(text: str) -> str:
    """Redact sensitive values from a string."""
    for pattern in _SENSITIVE_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact(record.getMessage()),
        }

        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id

        # Add extra fields
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "ip"):
            log_entry["ip"] = record.ip
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "path"):
            log_entry["path"] = record.path

        # Add exception info
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


def setup_logging(environment: str = "development", log_level: str = "INFO"):
    """Configure application-wide logging."""

    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler()

    if environment == "production":
        handler.setFormatter(JSONFormatter())
    else:
        # Human-readable format for development
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        ))

    root_logger.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every HTTP request with timing and correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        import time

        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4())[:8])
        start_time = time.time()

        # Attach correlation ID to request state
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Skip logging for static assets and health checks
        path = request.url.path
        if not (path.startswith("/assets") or path == "/health" or path.endswith(".js") or path.endswith(".css")):
            logger = logging.getLogger("app.requests")
            logger.info(
                f"{request.method} {path} → {response.status_code} ({duration_ms}ms)",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "ip": request.client.host if request.client else None,
                },
            )

        response.headers["X-Correlation-ID"] = correlation_id
        return response
