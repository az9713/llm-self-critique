import pytest

from src.critique.parser import CritiqueParser, CritiqueResult
from src.models.planning import Verdict


def test_parse_correct_verdict():
    response = """
    Step 1: (pickup A)
    Preconditions: (clear A), (on-table A), (arm-empty)
    All preconditions met. Applying action.
    State: arm holding A

    Step 2: (stack A B)
    Preconditions: (holding A), (clear B)
    All preconditions met. Applying action.
    State: A on B, arm empty

    Goal reached. the plan is correct
    """

    result = CritiqueParser.parse(response)

    assert result.verdict == Verdict.CORRECT
    assert len(result.step_traces) == 2


def test_parse_wrong_verdict():
    response = """
    Step 1: (pickup A)
    Preconditions: (clear A), (on-table A), (arm-empty)
    Check: (clear A)? NO - B is on top of A
    PRECONDITION FAILED

    the plan is wrong
    """

    result = CritiqueParser.parse(response)

    assert result.verdict == Verdict.WRONG
    assert "PRECONDITION FAILED" in result.error_reason


def test_parse_goal_not_reached():
    response = """
    All steps executed successfully.
    Final state: A on table, B on table
    Goal: A on B

    goal not reached
    """

    result = CritiqueParser.parse(response)

    assert result.verdict == Verdict.GOAL_NOT_REACHED
