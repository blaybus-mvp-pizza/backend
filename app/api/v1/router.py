from fastapi import APIRouter
from app.api.v1.endpoints import health, db_info

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(db_info.router, prefix="/db", tags=["db"])
