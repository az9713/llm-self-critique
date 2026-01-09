import pytest
from unittest.mock import AsyncMock, patch
import os

from src.llm.base import LLMRequest, LLMResponse, LLMProvider
from src.llm.router import LLMRouter


@pytest.fixture
def mock_adapters():
    with patch("src.llm.router.ClaudeAdapter") as claude_mock, \
         patch("src.llm.router.OpenAIAdapter") as openai_mock:

        claude_instance = AsyncMock()
        claude_instance.complete = AsyncMock(return_value=LLMResponse(
            content="Claude response",
            usage={"input_tokens": 10, "output_tokens": 20},
            latency_ms=100,
        ))
        claude_mock.return_value = claude_instance

        openai_instance = AsyncMock()
        openai_instance.complete = AsyncMock(return_value=LLMResponse(
            content="OpenAI response",
            usage={"input_tokens": 15, "output_tokens": 25},
            latency_ms=150,
        ))
        openai_mock.return_value = openai_instance

        yield {"claude": claude_instance, "openai": openai_instance}


async def test_router_routes_to_claude(mock_adapters):
    router = LLMRouter(api_keys={"claude": "test-key"})

    request = LLMRequest(prompt="Test", provider=LLMProvider.CLAUDE)
    response = await router.complete(request)

    assert response.content == "Claude response"
    mock_adapters["claude"].complete.assert_called_once()


async def test_router_routes_to_openai(mock_adapters):
    router = LLMRouter(api_keys={"openai": "test-key"})

    request = LLMRequest(prompt="Test", provider=LLMProvider.OPENAI)
    response = await router.complete(request)

    assert response.content == "OpenAI response"


async def test_router_missing_api_key():
    # Patch environment variables to ensure no API keys are found
    with patch.dict("os.environ", {}, clear=True), \
         patch("src.llm.router.os.getenv", return_value=None):
        router = LLMRouter(api_keys={})

        request = LLMRequest(prompt="Test", provider=LLMProvider.CLAUDE)

        with pytest.raises(ValueError, match="No API key configured"):
            await router.complete(request)
