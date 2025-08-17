from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db
from app.domains.products.product_list_item import ProductListItem
from app.domains.products.store_with_products import StoreWithProducts
from app.domains.products.store_meta import StoreMeta
from app.domains.products.service import ProductService


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


class ProductsAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get("/ending-soon", response_model=List[ProductListItem])
        async def get_ending_soon_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1),
            size: int = Query(4, ge=1, le=100),
        ):
            return service.ending_soon(page=page, size=size)

        @self.router.get("/recommended", response_model=List[ProductListItem])
        async def get_recommended_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1),
            size: int = Query(4, ge=1, le=100),
        ):
            return service.recommended(page=page, size=size)

        @self.router.get("/new", response_model=List[ProductListItem])
        async def get_new_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1),
            size: int = Query(4, ge=1, le=100),
        ):
            return service.newest(page=page, size=size)

        @self.router.get("/stores/recent", response_model=List[StoreWithProducts])
        async def get_recent_stores_with_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1),
            stores: int = Query(10, ge=1, le=50),
            size: int = Query(4, ge=1, le=100),
        ):
            return service.stores_recent(page=page, stores=stores, size=size)

        @self.router.get("/stores", response_model=List[StoreMeta])
        async def get_store_list(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1),
            size: int = Query(20, ge=1, le=100),
        ):
            return service.store_list(page=page, size=size)


api = ProductsAPI().router
