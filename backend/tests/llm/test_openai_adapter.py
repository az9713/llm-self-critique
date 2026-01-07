import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.base import LLMRequest, LLMProvider
from src.llm.adapters.openai import OpenAIAdapter


@pytest.fixture
def mock_openai():
    with patch("src.llm.adapters.openai.AsyncOpenAI") as mock:
        client = AsyncMock()
        mock.return_value = client

        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        response.usage.prompt_tokens = 10
        response.usage.completion_tokens = 20
        client.chat.completions.create = AsyncMock(return_value=response)

        yield client


async def test_openai_adapter_complete(mock_openai):
    adapter = OpenAIAdapter(api_key="test-key")

    request = LLMRequest(
        prompt="Test prompt",
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
    )

    response = await adapter.complete(request)

    assert response.content == "Test response"
    assert response.usage["input_tokens"] == 10


async def test_openai_adapter_default_model():
    adapter = OpenAIAdapter(api_key="test-key")
    assert adapter.default_model == "gpt-4o"
