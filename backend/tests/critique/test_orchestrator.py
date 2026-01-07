import pytest
from unittest.mock import AsyncMock, MagicMock

from src.critique.orchestrator import SelfCritiqueOrchestrator, PlanResult
from src.llm.base import LLMResponse, LLMProvider
from src.models.planning import Verdict


@pytest.fixture
def mock_router():
    router = AsyncMock()
    return router


@pytest.fixture
def orchestrator(mock_router):
    return SelfCritiqueOrchestrator(
        llm_router=mock_router,
        provider=LLMProvider.CLAUDE,
        max_iterations=3,
        num_critique_samples=5,
    )


async def test_plan_validates_on_first_try(orchestrator, mock_router):
    # Mock plan generation
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

    result = await orchestrator.run(
        domain_pddl="(define (domain test)...)",
        problem_pddl="(define (problem test)...)",
    )

    assert result.status == "valid"
    assert result.iterations == 1
    assert result.final_verdict == Verdict.CORRECT


async def test_plan_refines_after_critique(orchestrator, mock_router):
    mock_router.complete.side_effect = [
        # Iteration 1: Plan generation
        LLMResponse(content="1. pickup A", usage={}, latency_ms=100),
        # Iteration 1: 5 critiques - majority wrong
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        # Iteration 2: Refined plan
        LLMResponse(content="1. pickup A\n2. stack A B", usage={}, latency_ms=100),
        # Iteration 2: 5 critiques - all correct
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
    ]

    result = await orchestrator.run(
        domain_pddl="(define (domain test)...)",
        problem_pddl="(define (problem test)...)",
    )

    assert result.status == "valid"
    assert result.iterations == 2
