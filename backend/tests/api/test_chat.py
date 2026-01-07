import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.api.chat import _sessions


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear sessions before each test."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_start_session(client):
    response = await client.post("/api/v1/chat/start")

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["phase"] == "intro"
    assert data["is_complete"] is False


async def test_send_message(client):
    # Start session first
    start_response = await client.post("/api/v1/chat/start")
    session_id = start_response.json()["session_id"]

    # Send a message
    response = await client.post("/api/v1/chat/message", json={
        "session_id": session_id,
        "message": "I want to plan my morning routine",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "message" in data
    assert data["phase"] == "intro"


async def test_send_message_no_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat/message", json={
            "session_id": "nonexistent",
            "message": "Hello",
        })

        assert response.status_code == 404


async def test_get_session(client):
    # Start session first
    start_response = await client.post("/api/v1/chat/start")
    session_id = start_response.json()["session_id"]

    # Get session info
    response = await client.get(f"/api/v1/chat/session/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "phase" in data


async def test_delete_session(client):
    # Start session first
    start_response = await client.post("/api/v1/chat/start")
    session_id = start_response.json()["session_id"]

    # Delete session
    response = await client.delete(f"/api/v1/chat/session/{session_id}")
    assert response.status_code == 200

    # Verify session is gone
    get_response = await client.get(f"/api/v1/chat/session/{session_id}")
    assert get_response.status_code == 404
