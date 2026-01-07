import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.database import engine, Base, async_session_maker
from src.models import User, Workspace


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create test user and workspace
    async with async_session_maker() as session:
        user = User(email="test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        workspace = Workspace(name="Test", owner_id=user.id)
        session.add(workspace)
        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_create_domain(client):
    # First get workspace id
    async with async_session_maker() as session:
        from sqlalchemy import select
        from src.models import Workspace
        result = await session.execute(select(Workspace))
        workspace = result.scalar_one()
        workspace_id = str(workspace.id)

    response = await client.post("/api/v1/domains", json={
        "workspace_id": workspace_id,
        "name": "Morning Routine",
        "description": "Planning my morning tasks",
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Morning Routine"
    assert "id" in data


async def test_list_domains(client):
    response = await client.get("/api/v1/domains")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
