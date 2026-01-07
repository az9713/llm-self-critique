import pytest

from src.elicitation.state_machine import (
    ElicitationState,
    ElicitationPhase,
    ElicitationStateMachine,
)


def test_initial_state():
    state = ElicitationState()

    assert state.phase == ElicitationPhase.INTRO
    assert state.domain_name is None
    assert state.objects == []
    assert state.predicates == []
    assert state.actions == []


def test_state_machine_transitions():
    sm = ElicitationStateMachine()
    state = ElicitationState()

    # Transition from INTRO to OBJECTS
    state = sm.transition(state, ElicitationPhase.OBJECTS)
    assert state.phase == ElicitationPhase.OBJECTS

    # Transition to PREDICATES
    state = sm.transition(state, ElicitationPhase.PREDICATES)
    assert state.phase == ElicitationPhase.PREDICATES


def test_add_domain_info():
    state = ElicitationState()

    state.domain_name = "blocks-world"
    state.domain_description = "A domain for stacking blocks"
    state.objects = ["block_a", "block_b", "block_c"]
    state.predicates = ["on(?x, ?y)", "clear(?x)", "on-table(?x)", "holding(?x)"]
    state.actions = [
        {"name": "pickup", "params": ["?x"], "preconditions": ["clear(?x)", "on-table(?x)"], "effects": ["holding(?x)"]},
    ]

    assert state.domain_name == "blocks-world"
    assert len(state.objects) == 3
    assert len(state.predicates) == 4
    assert len(state.actions) == 1


def test_add_message():
    state = ElicitationState()

    state.add_message("user", "I want to plan my morning routine")
    state.add_message("assistant", "Great! Let me help you define your planning domain.")

    assert len(state.messages) == 2
    assert state.messages[0]["role"] == "user"
    assert state.messages[1]["role"] == "assistant"


def test_state_serialization():
    state = ElicitationState()
    state.domain_name = "test-domain"
    state.objects = ["obj1", "obj2"]
    state.add_message("user", "Hello")

    data = state.to_dict()

    assert data["domain_name"] == "test-domain"
    assert data["objects"] == ["obj1", "obj2"]
    assert len(data["messages"]) == 1

    # Deserialize
    restored = ElicitationState.from_dict(data)
    assert restored.domain_name == "test-domain"
    assert restored.objects == ["obj1", "obj2"]
