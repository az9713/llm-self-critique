"""Tests for analytics API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from src.main import app
from src.database import engine, Base, async_session_maker
from src.models import User
from src.models.analytics import UsageLog


client = TestClient(app)


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create test user and sample usage logs
    async with async_session_maker() as session:
        user = User(email="test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        # Create sample usage logs
        for i in range(10):
            log = UsageLog(
                user_id=user.id,
                endpoint="/api/v1/domains",
                method="GET",
                status_code=200 if i < 8 else 500,
                latency_ms=50 + i * 10,
                ip_address="192.168.1.1",
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            session.add(log)

        # Add LLM usage log
        llm_log = UsageLog(
            user_id=user.id,
            endpoint="/api/v1/planning",
            method="POST",
            status_code=200,
            latency_ms=1500,
            extra_data={
                "type": "llm_usage",
                "provider": "claude",
                "total_tokens": 500,
            },
        )
        session.add(llm_log)

        # Add planning session log
        planning_log = UsageLog(
            user_id=user.id,
            endpoint="/api/v1/planning/sessions",
            method="POST",
            status_code=200,
            latency_ms=5000,
            extra_data={
                "type": "planning_session",
                "iterations": 3,
                "status": "valid",
            },
        )
        session.add(planning_log)

        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestUsageSummary:
    def test_get_usage_summary(self):
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        data = response.json()

        assert "total_requests" in data
        assert "successful_requests" in data
        assert "failed_requests" in data
        assert "avg_latency_ms" in data
        assert data["total_requests"] >= 10

    def test_get_usage_summary_with_days(self):
        response = client.get("/api/v1/analytics/summary?days=7")
        assert response.status_code == 200

    def test_get_usage_summary_invalid_days(self):
        response = client.get("/api/v1/analytics/summary?days=0")
        assert response.status_code == 422  # Validation error


class TestEndpointStats:
    def test_get_endpoint_stats(self):
        response = client.get("/api/v1/analytics/endpoints")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "endpoint" in data[0]
            assert "request_count" in data[0]
            assert "avg_latency_ms" in data[0]
            assert "error_rate" in data[0]

    def test_get_endpoint_stats_with_limit(self):
        response = client.get("/api/v1/analytics/endpoints?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5


class TestDailyUsage:
    def test_get_daily_usage(self):
        response = client.get("/api/v1/analytics/daily")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "date" in data[0]
            assert "requests" in data[0]
            assert "avg_latency_ms" in data[0]


class TestAnalyticsDashboard:
    def test_get_dashboard(self):
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert "top_endpoints" in data
        assert "daily_usage" in data
        assert "period_start" in data
        assert "period_end" in data

    def test_get_dashboard_with_days(self):
        response = client.get("/api/v1/analytics/dashboard?days=7")
        assert response.status_code == 200


class TestRecentLogs:
    def test_get_recent_logs(self):
        response = client.get("/api/v1/analytics/recent")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "endpoint" in data[0]
            assert "method" in data[0]
            assert "status_code" in data[0]
            assert "latency_ms" in data[0]
            assert "created_at" in data[0]

    def test_get_recent_logs_with_limit(self):
        response = client.get("/api/v1/analytics/recent?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_get_recent_logs_filter_by_status(self):
        response = client.get("/api/v1/analytics/recent?status_code=500")
        assert response.status_code == 200
        data = response.json()
        for log in data:
            assert log["status_code"] == 500
