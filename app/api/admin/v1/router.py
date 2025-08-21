from fastapi import APIRouter
from app.api.v1.endpoints import admin_auctions, admin_products, admin_stores


admin_api_router = APIRouter()
admin_api_router.include_router(
    admin_auctions.api, prefix="/auctions", tags=["admin:auctions"]
)
admin_api_router.include_router(
    admin_stores.api, prefix="/stores", tags=["admin:stores"]
)
admin_api_router.include_router(
    admin_products.api, prefix="/products", tags=["admin:product"]
)
