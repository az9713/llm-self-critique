from fastapi import FastAPI

from src.api import api_router
from src.api.websocket import router as websocket_router
from src.api.chat_ws import router as chat_ws_router
from src.api.validation import router as validation_router
from src.api.analytics import router as analytics_router
from src.api.api_keys import router as api_keys_router
from src.middleware.usage_tracking import UsageTrackingMiddleware
from src.middleware.rate_limiting import RateLimitMiddleware

app = FastAPI(
    title="Self-Critique Planner API",
    description="LLM Planning Platform with Intrinsic Self-Critique",
    version="0.1.0",
)

# Add middleware (order matters: rate limiting first, then usage tracking)
app.add_middleware(UsageTrackingMiddleware, enabled=True)
app.add_middleware(RateLimitMiddleware, enabled=True, default_limit=100)

app.include_router(api_router)
app.include_router(websocket_router, tags=["websocket"])
app.include_router(chat_ws_router, tags=["chat-websocket"])
app.include_router(validation_router, tags=["validation"])
app.include_router(analytics_router, tags=["analytics"])
app.include_router(api_keys_router, tags=["api-keys"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
