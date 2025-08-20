from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    db_info,
    auth,
    products,
    product_detail,
    auction_actions,
    payments,
    stories,
    users,
    notifications,
)

api_router = APIRouter()
api_router.include_router(health.api, prefix="/health", tags=["health"])
api_router.include_router(db_info.router, prefix="/db", tags=["db"])
api_router.include_router(auth.api, prefix="/auth", tags=["auth"])

api_router.include_router(products.api, prefix="/products", tags=["products"])
api_router.include_router(product_detail.api, prefix="/catalog", tags=["catalog"])
api_router.include_router(auction_actions.api, prefix="/auction", tags=["auction"])
api_router.include_router(payments.api, prefix="/payments", tags=["payments"])
api_router.include_router(auth.api, prefix="/auth", tags=["auth"])
api_router.include_router(users.api, prefix="/users", tags=["users"])
api_router.include_router(stories.api, prefix="/stories", tags=["stories"])
api_router.include_router(notifications.api, prefix="/notifications", tags=["notifications"])
