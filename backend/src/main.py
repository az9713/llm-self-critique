from fastapi import FastAPI

from src.api import api_router

app = FastAPI(
    title="Self-Critique Planner API",
    description="LLM Planning Platform with Intrinsic Self-Critique",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
