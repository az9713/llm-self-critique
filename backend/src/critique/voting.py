from collections import Counter
from dataclasses import dataclass

from src.critique.parser import CritiqueResult
from src.models.planning import Verdict


@dataclass
class VoteResult:
    majority_verdict: Verdict
    breakdown: dict[Verdict, int]
    confidence: float
    is_low_confidence: bool
    best_critique: CritiqueResult


class VoteAggregator:
    LOW_CONFIDENCE_THRESHOLD = 0.8

    @classmethod
    def aggregate(cls, results: list[CritiqueResult]) -> VoteResult:
        verdicts = [r.verdict for r in results]
        counter = Counter(verdicts)

        majority_verdict, majority_count = counter.most_common(1)[0]
        confidence = majority_count / len(results)

        # Find best critique (first one with matching verdict)
        best_critique = next(r for r in results if r.verdict == majority_verdict)

        breakdown = {v: counter.get(v, 0) for v in Verdict}

        return VoteResult(
            majority_verdict=majority_verdict,
            breakdown=breakdown,
            confidence=confidence,
            is_low_confidence=confidence < cls.LOW_CONFIDENCE_THRESHOLD,
            best_critique=best_critique,
        )
