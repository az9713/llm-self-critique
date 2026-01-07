"""Tests for usage tracking middleware."""

import pytest
from datetime import datetime
from sqlalchemy import select
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.database import engine, Base, async_session_maker
from src.models import User
from src.models.analytics import UsageLog, APIKey, APIKeyStatus, UsageAggregate
from src.middleware.usage_tracking import UsageTrackingMiddleware, UsageTracker


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestAnalyticsModels:
    async def test_create_api_key(self):
        async with async_session_maker() as session:
            user = User(email="test@example.com", password_hash="hash")
            session.add(user)
            await session.flush()

            api_key = APIKey(
                user_id=user.id,
                name="Test Key",
                key_hash="hashed_key_value",
                key_prefix="sk-test1",
                rate_limit=100,
            )
            session.add(api_key)
            await session.commit()

            result = await session.execute(select(APIKey))
            saved = result.scalar_one()

            assert saved.name == "Test Key"
            assert saved.status == APIKeyStatus.ACTIVE
            assert saved.rate_limit == 100

    async def test_create_usage_log(self):
        async with async_session_maker() as session:
            log = UsageLog(
                endpoint="/api/v1/domains",
                method="GET",
                status_code=200,
                latency_ms=50,
                ip_address="192.168.1.1",
            )
            session.add(log)
            await session.commit()

            result = await session.execute(select(UsageLog))
            saved = result.scalar_one()

            assert saved.endpoint == "/api/v1/domains"
            assert saved.latency_ms == 50
            assert saved.created_at is not None

    async def test_create_usage_aggregate(self):
        async with async_session_maker() as session:
            aggregate = UsageAggregate(
                period_start=datetime.utcnow(),
                period_type="hour",
                total_requests=100,
                successful_requests=95,
                failed_requests=5,
                total_latency_ms=5000,
                avg_latency_ms=50.0,
                endpoints_breakdown={"/api/v1/domains": 50, "/api/v1/planning": 50},
            )
            session.add(aggregate)
            await session.commit()

            result = await session.execute(select(UsageAggregate))
            saved = result.scalar_one()

            assert saved.total_requests == 100
            assert saved.avg_latency_ms == 50.0


class TestUsageTrackingMiddleware:
    def test_middleware_tracks_request(self):
        app = FastAPI()
        app.add_middleware(UsageTrackingMiddleware, enabled=True)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/api/v1/test")

        assert response.status_code == 200

    def test_middleware_excludes_health_check(self):
        app = FastAPI()
        app.add_middleware(UsageTrackingMiddleware, enabled=True)

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200

    def test_middleware_disabled(self):
        app = FastAPI()
        app.add_middleware(UsageTrackingMiddleware, enabled=False)

        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/api/v1/test")

        assert response.status_code == 200


class TestUsageTracker:
    async def test_track_llm_usage(self):
        async with async_session_maker() as session:
            user = User(email="test@example.com", password_hash="hash")
            session.add(user)
            await session.commit()
            user_id = user.id

        await UsageTracker.track_llm_usage(
            user_id=user_id,
            provider="claude",
            model="claude-sonnet-4-20250514",
            input_tokens=100,
            output_tokens=200,
            latency_ms=1500,
        )

        async with async_session_maker() as session:
            result = await session.execute(
                select(UsageLog).where(UsageLog.user_id == user_id)
            )
            log = result.scalar_one()

            assert log.extra_data["type"] == "llm_usage"
            assert log.extra_data["provider"] == "claude"
            assert log.extra_data["total_tokens"] == 300

    async def test_track_planning_session(self):
        import uuid

        async with async_session_maker() as session:
            user = User(email="test2@example.com", password_hash="hash")
            session.add(user)
            await session.commit()
            user_id = user.id

        session_id = uuid.uuid4()
        domain_id = uuid.uuid4()

        await UsageTracker.track_planning_session(
            user_id=user_id,
            session_id=session_id,
            domain_id=domain_id,
            iterations=3,
            total_latency_ms=5000,
            status="valid",
        )

        async with async_session_maker() as session:
            result = await session.execute(
                select(UsageLog).where(UsageLog.user_id == user_id)
            )
            log = result.scalar_one()

            assert log.extra_data["type"] == "planning_session"
            assert log.extra_data["iterations"] == 3
            assert log.extra_data["status"] == "valid"
