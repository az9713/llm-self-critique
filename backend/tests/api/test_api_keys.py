"""Tests for API key management endpoints."""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from src.main import app
from src.database import engine, Base, async_session_maker
from src.models import User
from src.models.analytics import APIKey, APIKeyStatus


client = TestClient(app)


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create test user
    async with async_session_maker() as session:
        user = User(email="test@example.com", password_hash="hash")
        session.add(user)
        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user_id():
    """Get the test user ID."""
    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(select(User))
        user = result.scalar_one()
        return user.id


class TestCreateAPIKey:
    def test_create_api_key(self, test_user_id):
        response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Test Key", "rate_limit": 100}
        )
        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert data["name"] == "Test Key"
        assert "key" in data  # Raw key only returned on creation
        assert data["key"].startswith("sk_")
        assert data["key_prefix"] == data["key"][:8]
        assert data["status"] == "active"
        assert data["rate_limit"] == 100
        assert "warning" in data

    def test_create_api_key_custom_rate_limit(self, test_user_id):
        response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "High Rate Key", "rate_limit": 1000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rate_limit"] == 1000

    def test_create_api_key_with_expiry(self, test_user_id):
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Expiring Key", "rate_limit": 100, "expires_at": expires}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["expires_at"] is not None

    def test_create_api_key_invalid_rate_limit(self, test_user_id):
        response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Invalid Key", "rate_limit": 0}
        )
        assert response.status_code == 422

    def test_create_api_key_empty_name(self, test_user_id):
        response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "", "rate_limit": 100}
        )
        assert response.status_code == 422


class TestListAPIKeys:
    def test_list_api_keys(self, test_user_id):
        # Create some keys first
        for i in range(3):
            client.post(
                f"/api/v1/api-keys?user_id={test_user_id}",
                json={"name": f"Key {i}", "rate_limit": 100}
            )

        response = client.get(f"/api/v1/api-keys?user_id={test_user_id}")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 3
        # Keys should not include the raw key
        for key in data:
            assert "key" not in key
            assert "key_prefix" in key

    def test_list_api_keys_exclude_revoked(self, test_user_id):
        # Create and revoke a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "To Revoke", "rate_limit": 100}
        )
        key_id = create_response.json()["id"]
        client.delete(f"/api/v1/api-keys/{key_id}?user_id={test_user_id}")

        # List without revoked
        response = client.get(f"/api/v1/api-keys?user_id={test_user_id}")
        data = response.json()
        assert not any(k["id"] == key_id for k in data)

    def test_list_api_keys_include_revoked(self, test_user_id):
        # Create and revoke a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Revoked Key", "rate_limit": 100}
        )
        key_id = create_response.json()["id"]
        client.delete(f"/api/v1/api-keys/{key_id}?user_id={test_user_id}")

        # List with revoked
        response = client.get(
            f"/api/v1/api-keys?user_id={test_user_id}&include_revoked=true"
        )
        data = response.json()
        revoked_key = next((k for k in data if k["id"] == key_id), None)
        assert revoked_key is not None
        assert revoked_key["status"] == "revoked"


class TestGetAPIKey:
    def test_get_api_key(self, test_user_id):
        # Create a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Get Test Key", "rate_limit": 100}
        )
        key_id = create_response.json()["id"]

        # Get it
        response = client.get(
            f"/api/v1/api-keys/{key_id}?user_id={test_user_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == key_id
        assert data["name"] == "Get Test Key"

    def test_get_api_key_not_found(self, test_user_id):
        from uuid import uuid4
        response = client.get(
            f"/api/v1/api-keys/{uuid4()}?user_id={test_user_id}"
        )
        assert response.status_code == 404


class TestUpdateAPIKey:
    def test_update_api_key_name(self, test_user_id):
        # Create a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Original Name", "rate_limit": 100}
        )
        key_id = create_response.json()["id"]

        # Update name
        response = client.patch(
            f"/api/v1/api-keys/{key_id}?user_id={test_user_id}",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_api_key_rate_limit(self, test_user_id):
        # Create a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Rate Test", "rate_limit": 100}
        )
        key_id = create_response.json()["id"]

        # Update rate limit
        response = client.patch(
            f"/api/v1/api-keys/{key_id}?user_id={test_user_id}",
            json={"rate_limit": 500}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rate_limit"] == 500

    def test_update_api_key_status(self, test_user_id):
        # Create a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Status Test", "rate_limit": 100}
        )
        key_id = create_response.json()["id"]

        # Revoke via update
        response = client.patch(
            f"/api/v1/api-keys/{key_id}?user_id={test_user_id}",
            json={"status": "revoked"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "revoked"

        # Reactivate
        response = client.patch(
            f"/api/v1/api-keys/{key_id}?user_id={test_user_id}",
            json={"status": "active"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_update_api_key_invalid_status(self, test_user_id):
        # Create a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "Invalid Status Test", "rate_limit": 100}
        )
        key_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/api-keys/{key_id}?user_id={test_user_id}",
            json={"status": "invalid"}
        )
        assert response.status_code == 400


class TestRevokeAPIKey:
    def test_revoke_api_key(self, test_user_id):
        # Create a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "To Delete", "rate_limit": 100}
        )
        key_id = create_response.json()["id"]

        # Revoke it
        response = client.delete(
            f"/api/v1/api-keys/{key_id}?user_id={test_user_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "API key revoked successfully"

        # Verify it's revoked
        get_response = client.get(
            f"/api/v1/api-keys/{key_id}?user_id={test_user_id}"
        )
        assert get_response.json()["status"] == "revoked"


class TestRotateAPIKey:
    def test_rotate_api_key(self, test_user_id):
        # Create a key
        create_response = client.post(
            f"/api/v1/api-keys?user_id={test_user_id}",
            json={"name": "To Rotate", "rate_limit": 200}
        )
        old_key_id = create_response.json()["id"]
        old_key = create_response.json()["key"]

        # Rotate it
        response = client.post(
            f"/api/v1/api-keys/{old_key_id}/rotate?user_id={test_user_id}"
        )
        assert response.status_code == 200
        data = response.json()

        # New key should have new ID and key
        assert data["id"] != old_key_id
        assert data["key"] != old_key
        assert data["name"] == "To Rotate (rotated)"
        assert data["rate_limit"] == 200  # Same settings

        # Old key should be revoked
        old_key_response = client.get(
            f"/api/v1/api-keys/{old_key_id}?user_id={test_user_id}"
        )
        assert old_key_response.json()["status"] == "revoked"
