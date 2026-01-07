from fastapi import APIRouter

from src.api.domains import router as domains_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(domains_router, prefix="/domains", tags=["domains"])
