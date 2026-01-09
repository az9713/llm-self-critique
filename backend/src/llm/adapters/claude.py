import time
from anthropic import AsyncAnthropic

from src.llm.base import LLMRequest, LLMResponse


class ClaudeAdapter:
    default_model = "claude-haiku-4-5"

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()

        response = await self.client.messages.create(
            model=request.model or self.default_model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}],
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            latency_ms=latency_ms,
        )
