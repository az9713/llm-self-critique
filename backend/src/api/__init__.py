from fastapi import APIRouter

from src.api.domains import router as domains_router
from src.api.chat import router as chat_router
from src.api.planning import router as planning_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(domains_router, prefix="/domains", tags=["domains"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(planning_router, prefix="/sessions", tags=["planning"])
