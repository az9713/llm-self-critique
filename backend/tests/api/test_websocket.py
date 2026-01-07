import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.database import engine, Base, async_session_maker
from src.models import User, Workspace, Domain, PlanningSession
from src.models.planning import SessionStatus
from src.api.websocket import StreamingOrchestrator
from src.llm.base import LLMResponse, LLMProvider


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
        await session.flush()

        planning_session = PlanningSession(
            domain_id=domain.id,
            problem_description="Stack A on B",
            status=SessionStatus.ELICITING,
        )
        session.add(planning_session)
        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session_id():
    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(select(PlanningSession))
        planning_session = result.scalar_one()
        return str(planning_session.id)


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.fixture
def mock_router():
    router = AsyncMock()
    return router


async def test_streaming_orchestrator_sends_updates(mock_websocket, mock_router):
    """Test that StreamingOrchestrator sends WebSocket updates."""
    mock_router.complete.side_effect = [
        # Plan generation
        LLMResponse(content="1. pickup A\n2. stack A B", usage={}, latency_ms=100),
        # 5 critique samples - all correct
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
    ]

    orchestrator = StreamingOrchestrator(
        websocket=mock_websocket,
        llm_router=mock_router,
        provider=LLMProvider.CLAUDE,
        max_iterations=3,
        num_critique_samples=5,
    )

    result = await orchestrator.run(
        domain_pddl="(define (domain test)...)",
        problem_pddl="(define (problem test)...)",
    )

    assert result["status"] == "valid"
    assert result["iterations"] == 1

    # Verify WebSocket updates were sent
    assert mock_websocket.send_json.call_count > 0

    # Check for expected update types
    calls = [call.args[0]["type"] for call in mock_websocket.send_json.call_args_list]
    assert "started" in calls
    assert "iteration_started" in calls
    assert "generating_plan" in calls
    assert "plan_generated" in calls
    assert "critiquing" in calls
    assert "completed" in calls


async def test_streaming_orchestrator_multiple_iterations(mock_websocket, mock_router):
    """Test orchestrator with multiple iterations before success."""
    mock_router.complete.side_effect = [
        # Iteration 1: Plan
        LLMResponse(content="1. pickup A", usage={}, latency_ms=100),
        # Iteration 1: Critiques - majority wrong
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        # Iteration 2: Refined plan
        LLMResponse(content="1. pickup A\n2. stack A B", usage={}, latency_ms=100),
        # Iteration 2: Critiques - all correct
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
    ]

    orchestrator = StreamingOrchestrator(
        websocket=mock_websocket,
        llm_router=mock_router,
        provider=LLMProvider.CLAUDE,
        max_iterations=3,
        num_critique_samples=5,
    )

    result = await orchestrator.run(
        domain_pddl="(define (domain test)...)",
        problem_pddl="(define (problem test)...)",
    )

    assert result["status"] == "valid"
    assert result["iterations"] == 2

    # Verify iteration_complete was sent for first iteration
    calls = mock_websocket.send_json.call_args_list
    iteration_complete_calls = [c for c in calls if c.args[0]["type"] == "iteration_complete"]
    assert len(iteration_complete_calls) == 1


async def test_send_update(mock_websocket, mock_router):
    """Test the send_update method."""
    orchestrator = StreamingOrchestrator(
        websocket=mock_websocket,
        llm_router=mock_router,
        provider=LLMProvider.CLAUDE,
    )

    await orchestrator.send_update("test_event", {"key": "value"})

    mock_websocket.send_json.assert_called_once_with({
        "type": "test_event",
        "data": {"key": "value"},
    })
