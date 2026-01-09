from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # Load .env file before other imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.database import engine, Base
from src.models import *  # noqa: F401, F403 - Import all models to register them
from src.api.websocket import router as websocket_router
from src.api.chat_ws import router as chat_ws_router
from src.api.validation import router as validation_router
from src.api.analytics import router as analytics_router
from src.api.api_keys import router as api_keys_router
from src.middleware.usage_tracking import UsageTrackingMiddleware
from src.middleware.rate_limiting import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Self-Critique Planner API",
    description="LLM Planning Platform with Intrinsic Self-Critique",
    version="0.1.0",
    lifespan=lifespan,
)

# Add middleware (reverse order: last added = first executed)
# 1. Rate limiting and usage tracking
app.add_middleware(UsageTrackingMiddleware, enabled=True)
app.add_middleware(RateLimitMiddleware, enabled=True, default_limit=100)

# 2. CORS must be added last so it executes first (handles OPTIONS preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(websocket_router, tags=["websocket"])
app.include_router(chat_ws_router, tags=["chat-websocket"])
app.include_router(validation_router, tags=["validation"])
app.include_router(analytics_router, tags=["analytics"])
app.include_router(api_keys_router, tags=["api-keys"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
