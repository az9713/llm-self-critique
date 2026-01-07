import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.base import LLMRequest, LLMProvider
from src.llm.adapters.claude import ClaudeAdapter


@pytest.fixture
def mock_anthropic():
    with patch("src.llm.adapters.claude.AsyncAnthropic") as mock:
        client = AsyncMock()
        mock.return_value = client

        # Mock response
        response = MagicMock()
        response.content = [MagicMock(text="Test response")]
        response.usage.input_tokens = 10
        response.usage.output_tokens = 20
        client.messages.create = AsyncMock(return_value=response)

        yield client


async def test_claude_adapter_complete(mock_anthropic):
    adapter = ClaudeAdapter(api_key="test-key")

    request = LLMRequest(
        prompt="Test prompt",
        provider=LLMProvider.CLAUDE,
        model="claude-sonnet-4-20250514",
    )

    response = await adapter.complete(request)

    assert response.content == "Test response"
    assert response.usage["input_tokens"] == 10


async def test_claude_adapter_default_model():
    adapter = ClaudeAdapter(api_key="test-key")
    assert adapter.default_model == "claude-sonnet-4-20250514"
