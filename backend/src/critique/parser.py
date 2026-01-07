import re
from dataclasses import dataclass

from src.models.planning import Verdict


@dataclass
class CritiqueResult:
    verdict: Verdict
    step_traces: list[str]
    error_reason: str | None = None
    raw_response: str = ""


class CritiqueParser:
    VERDICT_PATTERNS = {
        Verdict.CORRECT: r"the plan is correct",
        Verdict.WRONG: r"the plan is wrong",
        Verdict.GOAL_NOT_REACHED: r"goal not reached",
    }

    @classmethod
    def parse(cls, response: str) -> CritiqueResult:
        verdict = cls._extract_verdict(response)
        step_traces = cls._extract_steps(response)
        error_reason = cls._extract_error(response) if verdict != Verdict.CORRECT else None

        return CritiqueResult(
            verdict=verdict,
            step_traces=step_traces,
            error_reason=error_reason,
            raw_response=response,
        )

    @classmethod
    def _extract_verdict(cls, response: str) -> Verdict:
        response_lower = response.lower()

        for verdict, pattern in cls.VERDICT_PATTERNS.items():
            if re.search(pattern, response_lower):
                return verdict

        return Verdict.WRONG  # Default to wrong if unclear

    @classmethod
    def _extract_steps(cls, response: str) -> list[str]:
        step_pattern = r"Step \d+:.*?(?=Step \d+:|$)"
        matches = re.findall(step_pattern, response, re.DOTALL | re.IGNORECASE)
        return [m.strip() for m in matches]

    @classmethod
    def _extract_error(cls, response: str) -> str | None:
        error_patterns = [
            r"PRECONDITION FAILED.*",
            r"Error:.*",
            r"Cannot.*",
        ]

        for pattern in error_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(0)

        return None
