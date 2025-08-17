from fastapi import APIRouter
from app.api.v1.endpoints import health, db_info, auth, users

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(db_info.router, prefix="/db", tags=["db"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.api, prefix="/users", tags=["users"])
