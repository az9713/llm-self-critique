import pytest

from src.elicitation.state_machine import ElicitationState, ElicitationPhase
from src.elicitation.completeness import CompletenessChecker, CompletenessReport


def test_incomplete_state_missing_all():
    state = ElicitationState()

    report = CompletenessChecker.check(state)

    assert not report.is_complete
    assert "domain_name" in report.missing
    assert "objects" in report.missing
    assert "actions" in report.missing


def test_incomplete_state_missing_actions():
    state = ElicitationState()
    state.domain_name = "blocks-world"
    state.objects = ["block_a", "block_b"]
    state.predicates = ["on(?x, ?y)", "clear(?x)"]

    report = CompletenessChecker.check(state)

    assert not report.is_complete
    assert "actions" in report.missing
    assert "domain_name" not in report.missing


def test_complete_state():
    state = ElicitationState()
    state.domain_name = "blocks-world"
    state.domain_description = "A domain for stacking blocks"
    state.objects = ["block_a", "block_b"]
    state.predicates = ["on(?x, ?y)", "clear(?x)", "on-table(?x)"]
    state.actions = [
        {
            "name": "pickup",
            "params": ["?x"],
            "preconditions": ["clear(?x)", "on-table(?x)"],
            "effects": ["+holding(?x)", "-on-table(?x)"],
        }
    ]
    state.initial_state = ["on-table(block_a)", "on-table(block_b)", "clear(block_a)", "clear(block_b)"]
    state.goal_state = ["on(block_a, block_b)"]

    report = CompletenessChecker.check(state)

    assert report.is_complete
    assert len(report.missing) == 0


def test_completeness_report_suggestions():
    state = ElicitationState()
    state.domain_name = "blocks-world"

    report = CompletenessChecker.check(state)

    assert len(report.suggestions) > 0
    assert any("object" in s.lower() for s in report.suggestions)


def test_get_next_phase():
    state = ElicitationState()
    state.phase = ElicitationPhase.INTRO

    next_phase = CompletenessChecker.get_next_phase(state)
    assert next_phase == ElicitationPhase.OBJECTS

    state.domain_name = "test"
    state.objects = ["a", "b"]
    state.phase = ElicitationPhase.OBJECTS

    next_phase = CompletenessChecker.get_next_phase(state)
    assert next_phase == ElicitationPhase.PREDICATES
