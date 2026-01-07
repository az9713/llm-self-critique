import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.database import engine, Base, async_session_maker
from src.models import User, Workspace, Domain, PlanningSession
from src.models.planning import SessionStatus, Verdict


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create test data
    async with async_session_maker() as session:
        user = User(email="test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        workspace = Workspace(name="Test", owner_id=user.id)
        session.add(workspace)
        await session.flush()

        domain = Domain(
            workspace_id=workspace.id,
            name="blocks-world",
            description="Block stacking domain",
        )
        session.add(domain)
        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def domain_id():
    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(select(Domain))
        domain = result.scalar_one()
        return str(domain.id)


async def test_create_session(client, domain_id):
    response = await client.post("/api/v1/sessions", json={
        "domain_id": domain_id,
        "problem_description": "Stack block A on block B",
    })

    assert response.status_code == 201
    data = response.json()
    assert data["domain_id"] == domain_id
    assert data["status"] == "eliciting"
    assert "id" in data


async def test_create_session_invalid_domain(client):
    response = await client.post("/api/v1/sessions", json={
        "domain_id": "00000000-0000-0000-0000-000000000000",
        "problem_description": "Test",
    })

    assert response.status_code == 404


async def test_list_sessions(client, domain_id):
    # Create a session first
    await client.post("/api/v1/sessions", json={
        "domain_id": domain_id,
        "problem_description": "Test problem",
    })

    response = await client.get("/api/v1/sessions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_list_sessions_filter_by_domain(client, domain_id):
    # Create a session
    await client.post("/api/v1/sessions", json={
        "domain_id": domain_id,
        "problem_description": "Test problem",
    })

    response = await client.get(f"/api/v1/sessions?domain_id={domain_id}")

    assert response.status_code == 200
    data = response.json()
    assert all(s["domain_id"] == domain_id for s in data)


async def test_get_session(client, domain_id):
    # Create a session
    create_response = await client.post("/api/v1/sessions", json={
        "domain_id": domain_id,
        "problem_description": "Test problem",
    })
    session_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json()["id"] == session_id


async def test_get_session_not_found(client):
    response = await client.get("/api/v1/sessions/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


async def test_delete_session(client, domain_id):
    # Create a session
    create_response = await client.post("/api/v1/sessions", json={
        "domain_id": domain_id,
        "problem_description": "Test problem",
    })
    session_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_response.status_code == 404


async def test_get_iterations_empty(client, domain_id):
    # Create a session
    create_response = await client.post("/api/v1/sessions", json={
        "domain_id": domain_id,
        "problem_description": "Test problem",
    })
    session_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/sessions/{session_id}/iterations")

    assert response.status_code == 200
    assert response.json() == []
