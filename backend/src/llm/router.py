import os

from src.llm.base import LLMRequest, LLMResponse, LLMProvider
from src.llm.adapters.claude import ClaudeAdapter
from src.llm.adapters.openai import OpenAIAdapter


class LLMRouter:
    def __init__(self, api_keys: dict[str, str] | None = None):
        self.adapters = {}

        # Use provided keys or fall back to environment variables
        if api_keys is None:
            api_keys = {}

        claude_key = api_keys.get("claude") or os.getenv("ANTHROPIC_API_KEY")
        openai_key = api_keys.get("openai") or os.getenv("OPENAI_API_KEY")

        if claude_key:
            self.adapters[LLMProvider.CLAUDE] = ClaudeAdapter(claude_key)
        if openai_key:
            self.adapters[LLMProvider.OPENAI] = OpenAIAdapter(openai_key)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if request.provider not in self.adapters:
            raise ValueError(f"No API key configured for provider: {request.provider}")

        adapter = self.adapters[request.provider]
        return await adapter.complete(request)
