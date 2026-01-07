"""Usage tracking middleware for API analytics."""

import time
import uuid
from datetime import datetime
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.database import async_session_maker
from src.models.analytics import UsageLog


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage metrics."""

    # Paths to exclude from tracking
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }

    def __init__(self, app: ASGIApp, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled or self._should_exclude(request.url.path):
            return await call_next(request)

        start_time = time.time()
        error_message: Optional[str] = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            status_code = 500
            raise
        finally:
            latency_ms = int((time.time() - start_time) * 1000)

            # Log usage asynchronously (don't block response)
            try:
                await self._log_usage(
                    request=request,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    error_message=error_message,
                )
            except Exception:
                # Don't let logging errors affect the response
                pass

        return response

    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded from tracking."""
        if path in self.EXCLUDED_PATHS:
            return True
        # Exclude static files
        if path.startswith("/static/") or path.startswith("/_next/"):
            return True
        return False

    async def _log_usage(
        self,
        request: Request,
        status_code: int,
        latency_ms: int,
        error_message: Optional[str] = None,
    ) -> None:
        """Log API usage to database."""
        # Extract user_id from request state if available (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        api_key_id = getattr(request.state, "api_key_id", None)

        # Get request size
        content_length = request.headers.get("content-length")
        request_size = int(content_length) if content_length else None

        # Get client IP (handle proxies)
        forwarded = request.headers.get("x-forwarded-for")
        ip_address = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None

        log_entry = UsageLog(
            user_id=user_id,
            api_key_id=api_key_id,
            endpoint=request.url.path,
            method=request.method,
            status_code=status_code,
            latency_ms=latency_ms,
            request_size=request_size,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            error_message=error_message,
            extra_data={
                "query_params": str(request.query_params) if request.query_params else None,
            },
        )

        async with async_session_maker() as session:
            session.add(log_entry)
            await session.commit()


class UsageTracker:
    """Utility class for tracking specific usage events."""

    @staticmethod
    async def track_llm_usage(
        user_id: uuid.UUID,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        endpoint: str = "/api/v1/planning",
    ) -> None:
        """Track LLM token usage."""
        log_entry = UsageLog(
            user_id=user_id,
            endpoint=endpoint,
            method="POST",
            status_code=200,
            latency_ms=latency_ms,
            extra_data={
                "type": "llm_usage",
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
        )

        async with async_session_maker() as session:
            session.add(log_entry)
            await session.commit()

    @staticmethod
    async def track_planning_session(
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        domain_id: uuid.UUID,
        iterations: int,
        total_latency_ms: int,
        status: str,
    ) -> None:
        """Track planning session completion."""
        log_entry = UsageLog(
            user_id=user_id,
            endpoint="/api/v1/planning/sessions",
            method="POST",
            status_code=200 if status == "valid" else 500,
            latency_ms=total_latency_ms,
            extra_data={
                "type": "planning_session",
                "session_id": str(session_id),
                "domain_id": str(domain_id),
                "iterations": iterations,
                "status": status,
            },
        )

        async with async_session_maker() as session:
            session.add(log_entry)
            await session.commit()
