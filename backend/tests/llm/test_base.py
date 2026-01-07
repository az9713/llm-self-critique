import pytest
from pydantic import ValidationError

from src.llm.base import LLMRequest, LLMResponse, LLMProvider


def test_llm_request_validation():
    request = LLMRequest(
        prompt="Test prompt",
        provider=LLMProvider.CLAUDE,
        model="claude-sonnet-4-20250514",
        temperature=0.7,
        max_tokens=1000,
    )
    assert request.provider == LLMProvider.CLAUDE


def test_llm_request_invalid_temperature():
    with pytest.raises(ValidationError):
        LLMRequest(
            prompt="Test",
            provider=LLMProvider.CLAUDE,
            temperature=2.5,  # Invalid: > 2.0
        )


def test_llm_response():
    response = LLMResponse(
        content="Test response",
        usage={"input_tokens": 10, "output_tokens": 20},
        latency_ms=150,
    )
    assert response.usage["input_tokens"] == 10
