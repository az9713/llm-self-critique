import time
from openai import AsyncOpenAI

from src.llm.base import LLMRequest, LLMResponse


class OpenAIAdapter:
    default_model = "gpt-4o"

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()

        response = await self.client.chat.completions.create(
            model=request.model or self.default_model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}],
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=response.choices[0].message.content,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            latency_ms=latency_ms,
        )
