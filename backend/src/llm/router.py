from src.llm.base import LLMRequest, LLMResponse, LLMProvider
from src.llm.adapters.claude import ClaudeAdapter
from src.llm.adapters.openai import OpenAIAdapter


class LLMRouter:
    def __init__(self, api_keys: dict[str, str]):
        self.adapters = {}

        if "claude" in api_keys:
            self.adapters[LLMProvider.CLAUDE] = ClaudeAdapter(api_keys["claude"])
        if "openai" in api_keys:
            self.adapters[LLMProvider.OPENAI] = OpenAIAdapter(api_keys["openai"])

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if request.provider not in self.adapters:
            raise ValueError(f"No API key configured for provider: {request.provider}")

        adapter = self.adapters[request.provider]
        return await adapter.complete(request)
