"""Tests for rate limiting middleware."""

import hashlib
import pytest
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.database import engine, Base, async_session_maker
from src.models import User
from src.models.analytics import APIKey, APIKeyStatus
from src.middleware.rate_limiting import (
    InMemoryRateLimiter,
    RateLimitMiddleware,
    check_api_key,
    require_api_key,
)


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestInMemoryRateLimiter:
    def test_basic_rate_limiting(self):
        limiter = InMemoryRateLimiter(window_seconds=60)

        # First request should pass
        is_limited, remaining, reset = limiter.is_rate_limited("test-key", limit=5)
        assert is_limited is False
        assert remaining == 4

    def test_rate_limit_exceeded(self):
        limiter = InMemoryRateLimiter(window_seconds=60)

        # Exhaust the limit
        for i in range(5):
            is_limited, _, _ = limiter.is_rate_limited("test-key", limit=5)
            if i < 5:
                assert is_limited is False

        # Next request should be limited
        is_limited, remaining, reset = limiter.is_rate_limited("test-key", limit=5)
        assert is_limited is True
        assert remaining == 0

    def test_different_keys_independent(self):
        limiter = InMemoryRateLimiter(window_seconds=60)

        # Exhaust limit for key1
        for _ in range(5):
            limiter.is_rate_limited("key1", limit=5)

        # key2 should still have full quota
        is_limited, remaining, _ = limiter.is_rate_limited("key2", limit=5)
        assert is_limited is False
        assert remaining == 4

    def test_get_usage(self):
        limiter = InMemoryRateLimiter(window_seconds=60)

        # Make some requests
        for _ in range(3):
            limiter.is_rate_limited("test-key", limit=10)

        count, reset = limiter.get_usage("test-key")
        assert count == 3
        assert reset <= 60


class TestRateLimitMiddleware:
    def test_middleware_adds_headers(self):
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, enabled=True, default_limit=100)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/api/v1/test")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_middleware_excludes_health(self):
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, enabled=True, default_limit=100)

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        # Health endpoint should not have rate limit headers
        assert "X-RateLimit-Limit" not in response.headers

    def test_middleware_disabled(self):
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, enabled=False, default_limit=100)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/api/v1/test")

        assert response.status_code == 200
        # Rate limit headers should not be present when disabled
        assert "X-RateLimit-Limit" not in response.headers

    def test_middleware_rate_limit_exceeded(self):
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, enabled=True, default_limit=3)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)

        # First 3 requests should succeed
        for _ in range(3):
            response = client.get("/api/v1/test")
            assert response.status_code == 200

        # 4th request should be rate limited
        response = client.get("/api/v1/test")
        assert response.status_code == 429
        assert "Retry-After" in response.headers

        data = response.json()
        assert data["detail"]["error"] == "rate_limit_exceeded"


class TestAPIKeyRateLimiting:
    async def test_api_key_rate_limit(self):
        """Test that API keys get their own rate limit."""
        # Create user and API key
        async with async_session_maker() as session:
            user = User(email="test@example.com", password_hash="hash")
            session.add(user)
            await session.flush()

            raw_key = "sk-test-key-12345"
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            api_key = APIKey(
                user_id=user.id,
                name="Test Key",
                key_hash=key_hash,
                key_prefix="sk-test1",
                rate_limit=200,  # Higher limit than default
            )
            session.add(api_key)
            await session.commit()

        # Test with middleware
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, enabled=True, default_limit=5)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)

        # With API key, should get higher limit
        response = client.get(
            "/api/v1/test",
            headers={"X-API-Key": raw_key}
        )
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "200"


class TestCheckAPIKey:
    async def test_check_api_key_valid(self):
        """Test check_api_key with valid key."""
        async with async_session_maker() as session:
            user = User(email="test@example.com", password_hash="hash")
            session.add(user)
            await session.flush()

            raw_key = "sk-test-key-valid"
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            api_key = APIKey(
                user_id=user.id,
                name="Test Key",
                key_hash=key_hash,
                key_prefix="sk-test",
                rate_limit=100,
            )
            session.add(api_key)
            await session.commit()
            expected_user_id = user.id

        # Create mock request
        from unittest.mock import MagicMock
        request = MagicMock()
        request.headers.get.return_value = raw_key

        result = await check_api_key(request)
        assert result == expected_user_id

    async def test_check_api_key_invalid(self):
        """Test check_api_key with invalid key."""
        from unittest.mock import MagicMock
        request = MagicMock()
        request.headers.get.return_value = "invalid-key"

        result = await check_api_key(request)
        assert result is None

    async def test_check_api_key_missing(self):
        """Test check_api_key with no key."""
        from unittest.mock import MagicMock
        request = MagicMock()
        request.headers.get.return_value = None

        result = await check_api_key(request)
        assert result is None


class TestRequireAPIKey:
    async def test_require_api_key_valid(self):
        """Test require_api_key with valid key."""
        async with async_session_maker() as session:
            user = User(email="test2@example.com", password_hash="hash")
            session.add(user)
            await session.flush()

            raw_key = "sk-test-key-require"
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            api_key = APIKey(
                user_id=user.id,
                name="Test Key",
                key_hash=key_hash,
                key_prefix="sk-test",
                rate_limit=100,
            )
            session.add(api_key)
            await session.commit()
            expected_user_id = user.id

        from unittest.mock import MagicMock
        request = MagicMock()
        request.headers.get.return_value = raw_key

        result = await require_api_key(request)
        assert result == expected_user_id

    async def test_require_api_key_missing_raises(self):
        """Test require_api_key raises with missing key."""
        from unittest.mock import MagicMock
        from fastapi import HTTPException

        request = MagicMock()
        request.headers.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await require_api_key(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"] == "invalid_api_key"


class TestAPIKeyStatus:
    async def test_inactive_key_rejected(self):
        """Test that inactive API keys are rejected."""
        async with async_session_maker() as session:
            user = User(email="test3@example.com", password_hash="hash")
            session.add(user)
            await session.flush()

            raw_key = "sk-test-key-inactive"
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            api_key = APIKey(
                user_id=user.id,
                name="Inactive Key",
                key_hash=key_hash,
                key_prefix="sk-test",
                rate_limit=100,
                status=APIKeyStatus.REVOKED,
            )
            session.add(api_key)
            await session.commit()

        from unittest.mock import MagicMock
        request = MagicMock()
        request.headers.get.return_value = raw_key

        result = await check_api_key(request)
        assert result is None  # Revoked key should not be valid
