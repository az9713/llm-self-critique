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
    response = await client.post("/api/v1/chat/start", json={})

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["phase"] == "intro"
    assert data["is_complete"] is False
    assert "messages" in data
    assert isinstance(data["messages"], list)


async def test_start_session_with_domain_id(client):
    # Note: domain_id won't be found in DB, but session should still start
    response = await client.post("/api/v1/chat/start", json={
        "domain_id": "00000000-0000-0000-0000-000000000001"
    })

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["domain_id"] == "00000000-0000-0000-0000-000000000001"


async def test_send_message(client):
    # Start session first
    start_response = await client.post("/api/v1/chat/start", json={})
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
    # Phase can transition based on LLM response, so check for valid phase
    valid_phases = ["intro", "objects", "predicates", "actions", "initial", "goal", "review", "complete"]
    assert data["phase"] in valid_phases


async def test_send_message_no_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat/message", json={
            "session_id": "nonexistent",
            "message": "Hello",
        })

        assert response.status_code == 404


async def test_get_session(client):
    # Start session first
    start_response = await client.post("/api/v1/chat/start", json={})
    session_id = start_response.json()["session_id"]

    # Get session info
    response = await client.get(f"/api/v1/chat/session/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "phase" in data
    assert "messages" in data
    assert isinstance(data["messages"], list)


async def test_get_session_with_messages(client):
    # Start session first
    start_response = await client.post("/api/v1/chat/start", json={})
    session_id = start_response.json()["session_id"]

    # Send a message to populate history
    await client.post("/api/v1/chat/message", json={
        "session_id": session_id,
        "message": "Hello",
    })

    # Get session info
    response = await client.get(f"/api/v1/chat/session/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) >= 2  # User message + assistant response


async def test_delete_session(client):
    # Start session first
    start_response = await client.post("/api/v1/chat/start", json={})
    session_id = start_response.json()["session_id"]

    # Delete session
    response = await client.delete(f"/api/v1/chat/session/{session_id}")
    assert response.status_code == 200

    # Verify session is gone
    get_response = await client.get(f"/api/v1/chat/session/{session_id}")
    assert get_response.status_code == 404
