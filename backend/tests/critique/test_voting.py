import pytest

from src.critique.voting import VoteAggregator, VoteResult
from src.critique.parser import CritiqueResult
from src.models.planning import Verdict


def test_majority_correct():
    results = [
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[]),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[]),
    ]

    vote = VoteAggregator.aggregate(results)

    assert vote.majority_verdict == Verdict.CORRECT
    assert vote.breakdown == {Verdict.CORRECT: 3, Verdict.WRONG: 2, Verdict.GOAL_NOT_REACHED: 0}
    assert vote.confidence == 0.6


def test_majority_wrong():
    results = [
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[], error_reason="Error 1"),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[], error_reason="Error 2"),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[], error_reason="Error 3"),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
    ]

    vote = VoteAggregator.aggregate(results)

    assert vote.majority_verdict == Verdict.WRONG
    assert vote.best_critique.error_reason == "Error 1"


def test_low_confidence_flag():
    results = [
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[]),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[]),
    ]

    vote = VoteAggregator.aggregate(results)

    assert vote.is_low_confidence is True  # 60% < 80% threshold
