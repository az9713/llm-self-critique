import pytest
from unittest.mock import AsyncMock

from src.elicitation.state_machine import ElicitationState
from src.elicitation.pddl_generator import PDDLGenerator
from src.llm.base import LLMResponse, LLMProvider


@pytest.fixture
def complete_state():
    state = ElicitationState()
    state.domain_name = "blocks-world"
    state.domain_description = "A domain for stacking blocks on a table"
    state.objects = ["block_a", "block_b", "table"]
    state.predicates = ["on(?x, ?y)", "clear(?x)", "on-table(?x)", "holding(?x)", "arm-empty"]
    state.actions = [
        {
            "name": "pickup",
            "params": ["?b - block"],
            "preconditions": ["clear(?b)", "on-table(?b)", "arm-empty"],
            "effects": ["+holding(?b)", "-on-table(?b)", "-clear(?b)", "-arm-empty"],
        },
        {
            "name": "putdown",
            "params": ["?b - block"],
            "preconditions": ["holding(?b)"],
            "effects": ["-holding(?b)", "+on-table(?b)", "+clear(?b)", "+arm-empty"],
        },
    ]
    state.initial_state = ["on-table(block_a)", "on-table(block_b)", "clear(block_a)", "clear(block_b)", "arm-empty"]
    state.goal_state = ["on(block_a, block_b)"]
    return state


@pytest.fixture
def mock_router():
    router = AsyncMock()
    return router


def test_build_domain_prompt(complete_state):
    generator = PDDLGenerator(llm_router=AsyncMock(), provider=LLMProvider.CLAUDE)

    prompt = generator._build_domain_prompt(complete_state)

    assert "blocks-world" in prompt
    assert "pickup" in prompt
    assert "on(?x, ?y)" in prompt


def test_build_problem_prompt(complete_state):
    generator = PDDLGenerator(llm_router=AsyncMock(), provider=LLMProvider.CLAUDE)

    prompt = generator._build_problem_prompt(complete_state, "(define (domain blocks-world)...)")

    assert "initial" in prompt.lower()
    assert "goal" in prompt.lower()
    assert "on(block_a, block_b)" in prompt


async def test_generate_domain(complete_state, mock_router):
    mock_router.complete.return_value = LLMResponse(
        content="""(define (domain blocks-world)
  (:predicates (on ?x ?y) (clear ?x) (on-table ?x) (holding ?x) (arm-empty))
  (:action pickup
    :parameters (?b - block)
    :precondition (and (clear ?b) (on-table ?b) (arm-empty))
    :effect (and (holding ?b) (not (on-table ?b)) (not (clear ?b)) (not (arm-empty)))))""",
        usage={"input_tokens": 100, "output_tokens": 200},
        latency_ms=500,
    )

    generator = PDDLGenerator(llm_router=mock_router, provider=LLMProvider.CLAUDE)
    result = await generator.generate_domain(complete_state)

    assert "(define (domain blocks-world)" in result
    assert "(:action pickup" in result


async def test_generate_problem(complete_state, mock_router):
    domain_pddl = "(define (domain blocks-world)...)"
    mock_router.complete.return_value = LLMResponse(
        content="""(define (problem blocks-problem)
  (:domain blocks-world)
  (:objects block_a block_b - block)
  (:init (on-table block_a) (on-table block_b) (clear block_a) (clear block_b) (arm-empty))
  (:goal (on block_a block_b)))""",
        usage={"input_tokens": 100, "output_tokens": 150},
        latency_ms=400,
    )

    generator = PDDLGenerator(llm_router=mock_router, provider=LLMProvider.CLAUDE)
    result = await generator.generate_problem(complete_state, domain_pddl)

    assert "(define (problem" in result
    assert "(:goal" in result
