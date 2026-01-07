from enum import Enum
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"


class LLMRequest(BaseModel):
    prompt: str
    provider: LLMProvider
    model: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=100000)
    stream: bool = False


class LLMResponse(BaseModel):
    content: str
    usage: dict
    latency_ms: int
    provider_metadata: dict | None = None
