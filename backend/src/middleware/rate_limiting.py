"""Rate limiting middleware for API protection."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy import select

from src.database import async_session_maker
from src.models.analytics import APIKey, APIKeyStatus


@dataclass
class RateLimitEntry:
    """Track request counts for rate limiting."""
    count: int = 0
    window_start: float = field(default_factory=time.time)


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window."""

    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._buckets: dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)

    def is_rate_limited(self, key: str, limit: int) -> tuple[bool, int, int]:
        """
        Check if key is rate limited.

        Returns:
            tuple of (is_limited, remaining, reset_seconds)
        """
        now = time.time()
        entry = self._buckets[key]

        # Reset window if expired
        if now - entry.window_start >= self.window_seconds:
            entry.count = 0
            entry.window_start = now

        # Check limit
        remaining = max(0, limit - entry.count)
        reset_seconds = int(self.window_seconds - (now - entry.window_start))

        if entry.count >= limit:
            return True, 0, reset_seconds

        # Increment counter
        entry.count += 1
        remaining = max(0, limit - entry.count)

        return False, remaining, reset_seconds

    def get_usage(self, key: str) -> tuple[int, int]:
        """Get current usage for a key."""
        now = time.time()
        entry = self._buckets[key]

        if now - entry.window_start >= self.window_seconds:
            return 0, self.window_seconds

        reset_seconds = int(self.window_seconds - (now - entry.window_start))
        return entry.count, reset_seconds


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter(window_seconds=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits."""

    # Default limits for unauthenticated requests
    DEFAULT_RATE_LIMIT = 60  # requests per minute

    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }

    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
        default_limit: int = 60,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.default_limit = default_limit
        self.rate_limiter = InMemoryRateLimiter(window_seconds=window_seconds)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled or self._should_exclude(request.url.path):
            return await call_next(request)

        # Determine rate limit key and limit
        key, limit = await self._get_rate_limit_info(request)

        # Check rate limit
        is_limited, remaining, reset_seconds = self.rate_limiter.is_rate_limited(
            key, limit
        )

        if is_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": {
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Try again in {reset_seconds} seconds.",
                        "retry_after": reset_seconds,
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seconds),
                    "Retry-After": str(reset_seconds),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)

        return response

    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded from rate limiting."""
        if path in self.EXCLUDED_PATHS:
            return True
        if path.startswith("/static/") or path.startswith("/_next/"):
            return True
        return False

    async def _get_rate_limit_info(self, request: Request) -> tuple[str, int]:
        """
        Get rate limit key and limit for request.

        Uses API key if present, otherwise falls back to IP address.
        """
        # Check for API key in header
        api_key_header = request.headers.get("X-API-Key")

        if api_key_header:
            api_key_info = await self._validate_api_key(api_key_header)
            if api_key_info:
                api_key_id, rate_limit = api_key_info
                # Store API key info in request state for downstream use
                request.state.api_key_id = api_key_id
                return f"apikey:{api_key_id}", rate_limit

        # Fall back to IP-based rate limiting
        ip = self._get_client_ip(request)
        return f"ip:{ip}", self.default_limit

    async def _validate_api_key(self, key_value: str) -> Optional[tuple[UUID, int]]:
        """
        Validate API key and return (key_id, rate_limit) if valid.
        """
        import hashlib

        # Hash the key for lookup
        key_hash = hashlib.sha256(key_value.encode()).hexdigest()

        async with async_session_maker() as session:
            result = await session.execute(
                select(APIKey).where(
                    APIKey.key_hash == key_hash,
                    APIKey.status == APIKeyStatus.ACTIVE,
                )
            )
            api_key = result.scalar_one_or_none()

            if api_key:
                # Update last used timestamp
                api_key.last_used_at = datetime.now(timezone.utc)
                await session.commit()
                return api_key.id, api_key.rate_limit

        return None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP, handling proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"


async def check_api_key(request: Request) -> Optional[UUID]:
    """
    Dependency to check API key and return user_id if valid.

    Usage:
        @router.get("/endpoint")
        async def endpoint(api_key_user: Optional[UUID] = Depends(check_api_key)):
            if api_key_user:
                # Authenticated via API key
            else:
                # Unauthenticated
    """
    import hashlib

    api_key_header = request.headers.get("X-API-Key")
    if not api_key_header:
        return None

    key_hash = hashlib.sha256(api_key_header.encode()).hexdigest()

    async with async_session_maker() as session:
        result = await session.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.status == APIKeyStatus.ACTIVE,
            )
        )
        api_key = result.scalar_one_or_none()

        if api_key:
            api_key.last_used_at = datetime.now(timezone.utc)
            await session.commit()
            return api_key.user_id

    return None


async def require_api_key(request: Request) -> UUID:
    """
    Dependency that requires a valid API key.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(user_id: UUID = Depends(require_api_key)):
            # Guaranteed to have valid user_id
    """
    user_id = await check_api_key(request)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_api_key",
                "message": "Valid API key required. Include X-API-Key header.",
            },
        )
    return user_id
