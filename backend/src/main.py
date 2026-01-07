from fastapi import FastAPI

from src.api import api_router
from src.api.websocket import router as websocket_router

app = FastAPI(
    title="Self-Critique Planner API",
    description="LLM Planning Platform with Intrinsic Self-Critique",
    version="0.1.0",
)

app.include_router(api_router)
app.include_router(websocket_router, tags=["websocket"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
